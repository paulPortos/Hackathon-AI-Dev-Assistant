import importlib
from datetime import datetime, time
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from projects.models import Project, ProjectAuditLog, ProjectMember, ProjectTask
from projects.selectors import project_get_agent_context
from projects.services import (
    project_task_create,
    project_vulnerability_create,
    project_vulnerability_mark_resolved,
)
from user_descriptions.models import UserDescription
from users.models import User


project_import_service_module = importlib.import_module('projects.services.project_import_from_github')
project_github_repository_list_service_module = importlib.import_module('projects.services.project_github_repository_list')
project_repository_branch_list_service_module = importlib.import_module('projects.services.project_repository_branch_list')


class ProjectTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            github_id='1',
            username='creator',
            name='Project Creator',
            email='creator@example.com',
            access_token='creator-github-token',
        )
        self.member = User.objects.create_user(
            github_id='2',
            username='backend-dev',
            name='Backend Dev',
            email='backend@example.com',
            access_token='member-github-token',
        )
        self.outsider = User.objects.create_user(
            github_id='3',
            username='outsider',
            name='Outsider',
            email='outsider@example.com',
            access_token='outsider-github-token',
        )

    def auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}

    def create_project(self, creator=None):
        project = Project.objects.create(
            creator=creator or self.creator,
            github_repo_id=123,
            github_full_name='octocat/hello-world',
            github_html_url='https://github.com/octocat/hello-world',
            github_clone_url='https://github.com/octocat/hello-world.git',
            github_default_branch='main',
            github_visibility='public',
            github_primary_language='Python',
            github_languages={'Python': 1000},
            github_description='A test repository',
        )
        ProjectMember.objects.create(project=project, user=project.creator, invited_by=project.creator, display_role='Owner', roles=['owner'])
        return project

    def github_repo_payload(self, description='A test repository'):
        return {
            'id': 123,
            'full_name': 'octocat/hello-world',
            'html_url': 'https://github.com/octocat/hello-world',
            'clone_url': 'https://github.com/octocat/hello-world.git',
            'default_branch': 'main',
            'visibility': 'public',
            'language': 'Python',
            'description': description,
            'private': False,
        }

    def test_import_from_github_creates_project_and_owner_membership(self):
        with patch.object(project_import_service_module, 'fetch_github_repository') as fetch_repo:
            with patch.object(project_import_service_module, 'fetch_github_repository_languages') as fetch_languages:
                fetch_repo.return_value = self.github_repo_payload()
                fetch_languages.return_value = {'Python': 1000, 'JavaScript': 500}

                response = self.client.post(
                    reverse('api:projects:project-import-from-github', kwargs={'version': 'v1'}),
                    {'repository': 'octocat/hello-world'},
                    content_type='application/json',
                    **self.auth_header(self.creator),
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['github_full_name'], 'octocat/hello-world')
        self.assertEqual(payload['github_languages'], {'Python': 1000, 'JavaScript': 500})
        self.assertEqual(Project.objects.count(), 1)
        owner_membership = ProjectMember.objects.get(project_id=payload['id'], user=self.creator)
        self.assertEqual(owner_membership.display_role, 'Owner')
        self.assertEqual(owner_membership.roles, ['owner'])

    def test_import_from_github_refreshes_existing_creator_repo(self):
        self.create_project()

        with patch.object(project_import_service_module, 'fetch_github_repository') as fetch_repo:
            with patch.object(project_import_service_module, 'fetch_github_repository_languages') as fetch_languages:
                fetch_repo.return_value = self.github_repo_payload(description='Updated from GitHub')
                fetch_languages.return_value = {'Python': 2000}

                response = self.client.post(
                    reverse('api:projects:project-import-from-github', kwargs={'version': 'v1'}),
                    {'repository': 'octocat/hello-world'},
                    content_type='application/json',
                    **self.auth_header(self.creator),
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.get()
        self.assertEqual(project.github_description, 'Updated from GitHub')
        self.assertEqual(project.github_languages, {'Python': 2000})

    def test_import_from_github_requires_connected_token_and_owner_name_format(self):
        self.creator.access_token = ''
        self.creator.save(update_fields=['access_token', 'updated_at'])

        missing_token_response = self.client.post(
            reverse('api:projects:project-import-from-github', kwargs={'version': 'v1'}),
            {'repository': 'octocat/hello-world'},
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        invalid_format_response = self.client.post(
            reverse('api:projects:project-import-from-github', kwargs={'version': 'v1'}),
            {'repository': 'https://github.com/octocat/hello-world'},
            content_type='application/json',
            **self.auth_header(self.creator),
        )

        self.assertEqual(missing_token_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid_format_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_project_list_is_paginated_and_scoped_to_memberships(self):
        visible_project = self.create_project()
        hidden_project = self.create_project(creator=self.outsider)
        hidden_project.github_repo_id = 999
        hidden_project.github_full_name = 'octocat/private-world'
        hidden_project.save(update_fields=['github_repo_id', 'github_full_name', 'updated_at'])

        response = self.client.get(
            reverse('api:projects:project-list', kwargs={'version': 'v1'}),
            **self.auth_header(self.creator),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['count'], 1)
        self.assertEqual(payload['results'][0]['id'], visible_project.id)

    def test_github_repository_list_returns_paginated_repositories(self):
        with patch.object(
            project_github_repository_list_service_module,
            'fetch_github_repository_list',
        ) as fetch_repositories:
            fetch_repositories.return_value = [
                {
                    'id': 123,
                    'name': 'hello-world',
                    'full_name': 'octocat/hello-world',
                    'owner': {
                        'login': 'octocat',
                        'avatar_url': 'https://avatars.githubusercontent.com/u/1',
                    },
                    'html_url': 'https://github.com/octocat/hello-world',
                    'clone_url': 'https://github.com/octocat/hello-world.git',
                    'default_branch': 'main',
                    'visibility': 'public',
                    'language': 'Python',
                    'description': 'A test repository',
                    'private': False,
                    'fork': False,
                    'archived': False,
                    'updated_at': '2026-05-04T12:00:00Z',
                },
                {
                    'id': 456,
                    'name': 'private-world',
                    'full_name': 'octocat/private-world',
                    'owner': {'login': 'octocat'},
                    'html_url': 'https://github.com/octocat/private-world',
                    'private': True,
                    'fork': True,
                    'archived': True,
                },
            ]

            response = self.client.get(
                reverse('api:projects:github-repository-list', kwargs={'version': 'v1'}),
                **self.auth_header(self.creator),
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['count'], 2)
        self.assertEqual(payload['results'][0]['github_repo_id'], 123)
        self.assertEqual(payload['results'][0]['full_name'], 'octocat/hello-world')
        self.assertEqual(payload['results'][0]['owner_login'], 'octocat')
        self.assertEqual(payload['results'][0]['primary_language'], 'Python')
        self.assertFalse(payload['results'][0]['is_private'])
        self.assertTrue(payload['results'][1]['is_private'])
        self.assertNotIn('access_token', payload['results'][0])
        fetch_repositories.assert_called_once_with(access_token='creator-github-token')

    def test_github_repository_list_requires_connected_token(self):
        self.creator.access_token = ''
        self.creator.save(update_fields=['access_token', 'updated_at'])

        with patch.object(
            project_github_repository_list_service_module,
            'fetch_github_repository_list',
        ) as fetch_repositories:
            response = self.client.get(
                reverse('api:projects:github-repository-list', kwargs={'version': 'v1'}),
                **self.auth_header(self.creator),
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'GitHub account must be connected before listing repositories')
        self.assertEqual(response.json()['code'], 'github_token_missing')
        fetch_repositories.assert_not_called()

    def test_github_repository_list_rejects_malformed_github_payload(self):
        with patch.object(
            project_github_repository_list_service_module,
            'fetch_github_repository_list',
        ) as fetch_repositories:
            fetch_repositories.return_value = [{'name': 'missing-required-fields'}]

            response = self.client.get(
                reverse('api:projects:github-repository-list', kwargs={'version': 'v1'}),
                **self.auth_header(self.creator),
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'GitHub repository list fetch returned an invalid response')

    def test_project_repository_branch_list_returns_default_branch_and_commit_shas(self):
        project = self.create_project()
        ProjectMember.objects.create(project=project, user=self.member, invited_by=self.creator, display_role='Backend Developer', roles=['backend'])

        with patch.object(project_repository_branch_list_service_module, 'fetch_github_repository_branches') as fetch_branches:
            fetch_branches.return_value = [
                {'name': 'main', 'commit': {'sha': 'main-sha'}},
                {'name': 'feature/auth', 'commit': {'sha': 'feature-sha'}},
            ]

            response = self.client.get(
                reverse('api:projects:project-repository-branch-list', kwargs={'version': 'v1', 'project_id': project.id}),
                **self.auth_header(self.member),
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['default_branch'], 'main')
        self.assertEqual(
            payload['branches'],
            [
                {'name': 'main', 'commit_sha': 'main-sha', 'is_default': True},
                {'name': 'feature/auth', 'commit_sha': 'feature-sha', 'is_default': False},
            ],
        )
        fetch_branches.assert_called_once_with(access_token='creator-github-token', repository='octocat/hello-world')

    def test_project_repository_branch_list_is_member_scoped(self):
        project = self.create_project()

        with patch.object(project_repository_branch_list_service_module, 'fetch_github_repository_branches') as fetch_branches:
            response = self.client.get(
                reverse('api:projects:project-repository-branch-list', kwargs={'version': 'v1', 'project_id': project.id}),
                **self.auth_header(self.outsider),
            )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        fetch_branches.assert_not_called()

    def test_project_repository_branch_list_requires_creator_github_token(self):
        project = self.create_project()
        self.creator.access_token = ''
        self.creator.save(update_fields=['access_token', 'updated_at'])

        with patch.object(project_repository_branch_list_service_module, 'fetch_github_repository_branches') as fetch_branches:
            response = self.client.get(
                reverse('api:projects:project-repository-branch-list', kwargs={'version': 'v1', 'project_id': project.id}),
                **self.auth_header(self.creator),
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'GitHub account must be connected before reading repository code')
        self.assertEqual(response.json()['code'], 'github_token_missing')
        fetch_branches.assert_not_called()

    def test_project_repository_branch_list_rejects_malformed_github_payload(self):
        project = self.create_project()

        with patch.object(project_repository_branch_list_service_module, 'fetch_github_repository_branches') as fetch_branches:
            fetch_branches.return_value = [{'name': 'main', 'commit': {}}]

            response = self.client.get(
                reverse('api:projects:project-repository-branch-list', kwargs={'version': 'v1', 'project_id': project.id}),
                **self.auth_header(self.creator),
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'GitHub repository branches fetch returned an invalid response')

    def test_project_detail_read_and_creator_context_update_permissions(self):
        project = self.create_project()
        ProjectMember.objects.create(project=project, user=self.member, invited_by=self.creator, display_role='Backend Developer', roles=['backend'])

        read_response = self.client.get(
            reverse('api:projects:project-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            **self.auth_header(self.member),
        )
        update_response = self.client.patch(
            reverse('api:projects:project-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            {
                'overview': 'Security review assistant project',
                'goals': 'Find risky implementation gaps',
                'tech_stack': ['Django', 'DRF', 'PostgreSQL', 'Django'],
                'business_context': 'Hackathon MVP',
                'agent_notes': 'Ask about auth, CORS, scaling, and task priority.',
            },
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        forbidden_response = self.client.patch(
            reverse('api:projects:project-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            {'overview': 'Not allowed'},
            content_type='application/json',
            **self.auth_header(self.member),
        )

        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)
        project.refresh_from_db()
        self.assertEqual(project.tech_stack, ['Django', 'DRF', 'PostgreSQL'])
        self.assertEqual(project.overview, 'Security review assistant project')

    def test_creator_can_invite_update_and_remove_existing_members(self):
        project = self.create_project()

        invite_response = self.client.post(
            reverse('api:projects:project-member-list', kwargs={'version': 'v1', 'project_id': project.id}),
            {'user_id': self.member.id, 'display_role': 'Backend Developer', 'roles': ['backend', 'api', 'backend']},
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        project_member = ProjectMember.objects.get(project=project, user=self.member)
        update_response = self.client.patch(
            reverse(
                'api:projects:project-member-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'member_id': project_member.id},
            ),
            {'display_role': 'Solutions Architect', 'roles': ['architecture', 'security']},
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        delete_response = self.client.delete(
            reverse(
                'api:projects:project-member-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'member_id': project_member.id},
            ),
            **self.auth_header(self.creator),
        )

        self.assertEqual(invite_response.status_code, status.HTTP_200_OK)
        self.assertEqual(invite_response.json()['roles'], ['backend', 'api'])
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.json()['display_role'], 'Solutions Architect')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectMember.objects.filter(project=project, user=self.member).exists())

    def test_member_invite_rejects_duplicate_missing_user_and_non_creator(self):
        project = self.create_project()
        ProjectMember.objects.create(project=project, user=self.member, invited_by=self.creator, display_role='Backend Developer', roles=['backend'])

        duplicate_response = self.client.post(
            reverse('api:projects:project-member-list', kwargs={'version': 'v1', 'project_id': project.id}),
            {'user_id': self.member.id, 'display_role': 'Backend Developer', 'roles': ['backend']},
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        missing_user_response = self.client.post(
            reverse('api:projects:project-member-list', kwargs={'version': 'v1', 'project_id': project.id}),
            {'user_id': 9999, 'display_role': 'Security Engineer', 'roles': ['security']},
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        non_creator_response = self.client.post(
            reverse('api:projects:project-member-list', kwargs={'version': 'v1', 'project_id': project.id}),
            {'user_id': self.outsider.id, 'display_role': 'QA', 'roles': ['qa']},
            content_type='application/json',
            **self.auth_header(self.member),
        )

        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(missing_user_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(non_creator_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creator_membership_cannot_be_removed(self):
        project = self.create_project()
        owner_membership = ProjectMember.objects.get(project=project, user=self.creator)

        response = self.client.delete(
            reverse(
                'api:projects:project-member-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'member_id': owner_membership.id},
            ),
            **self.auth_header(self.creator),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(ProjectMember.objects.filter(id=owner_membership.id).exists())

    def test_vulnerabilities_are_readable_by_members_and_created_by_internal_service(self):
        project = self.create_project()
        ProjectMember.objects.create(project=project, user=self.member, invited_by=self.creator, display_role='Security Engineer', roles=['security'])
        vulnerability = project_vulnerability_create(
            project=project,
            data={
                'agent_name': 'SR Dev Agent',
                'source': 'conversation_review',
                'title': 'Missing CORS review',
                'summary': 'The project has not documented CORS behavior.',
                'severity': 'medium',
                'category': 'security',
                'affected_area': 'backend',
                'affected_path': 'server/config/settings.py',
                'evidence': {'question': 'Did you configure CORS?'},
                'recommendation': 'Add explicit CORS policy before deployment.',
            },
        )

        list_response = self.client.get(
            reverse('api:projects:project-vulnerability-list', kwargs={'version': 'v1', 'project_id': project.id}),
            **self.auth_header(self.member),
        )
        detail_response = self.client.get(
            reverse(
                'api:projects:project-vulnerability-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'vulnerability_id': vulnerability.id},
            ),
            **self.auth_header(self.member),
        )
        create_response = self.client.post(
            reverse('api:projects:project-vulnerability-list', kwargs={'version': 'v1', 'project_id': project.id}),
            {'title': 'Should not be public'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        outsider_response = self.client.get(
            reverse('api:projects:project-vulnerability-list', kwargs={'version': 'v1', 'project_id': project.id}),
            **self.auth_header(self.outsider),
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.json()['count'], 1)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.json()['title'], 'Missing CORS review')
        self.assertEqual(create_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(outsider_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_project_agent_context_includes_repo_context_members_and_user_descriptions(self):
        project = self.create_project()
        ProjectMember.objects.create(project=project, user=self.member, invited_by=self.creator, display_role='Backend Developer', roles=['backend'])
        UserDescription.objects.create(
            user=self.member,
            primary_role='backend',
            experience_level='mid',
            summary='Builds Django APIs.',
            skills=[{'name': 'Django', 'level': 4}],
            preferred_tasks=['backend_api'],
            avoided_tasks=['frontend_ui'],
        )

        context = project_get_agent_context(project)

        self.assertEqual(context['project']['github_full_name'], 'octocat/hello-world')
        self.assertEqual(context['members'][1]['display_role'], 'Backend Developer')
        self.assertEqual(context['members'][1]['user_description']['primary_role'], 'backend')

    def test_internal_task_create_stores_assignment_finding_priority_and_reasoning(self):
        project = self.create_project()
        project_member = ProjectMember.objects.create(
            project=project,
            user=self.member,
            invited_by=self.creator,
            display_role='Backend Developer',
            roles=['backend'],
        )
        vulnerability = project_vulnerability_create(
            project=project,
            data={'title': 'Hardcoded secret', 'severity': 'critical', 'status': 'open'},
        )

        project_task = project_task_create(
            project=project,
            data={
                'assigned_to': project_member,
                'related_finding': vulnerability,
                'title': 'Remove hardcoded secret',
                'description': 'Move the secret into environment variables.',
                'category': 'vulnerability_fix',
                'priority': 'critical',
                'status': 'todo',
                'created_by_agent': 'PM Agent',
                'reasoning': 'Security vulnerability should be fixed before release.',
            },
        )

        self.assertEqual(project_task.assigned_to, project_member)
        self.assertEqual(project_task.related_finding, vulnerability)
        self.assertEqual(project_task.priority, 'critical')
        self.assertEqual(project_task.reasoning, 'Security vulnerability should be fixed before release.')

    def test_task_list_detail_and_update_permissions(self):
        project = self.create_project()
        project_member = ProjectMember.objects.create(
            project=project,
            user=self.member,
            invited_by=self.creator,
            display_role='Backend Developer',
            roles=['backend'],
        )
        owner_membership = ProjectMember.objects.get(project=project, user=self.creator)
        project_task = project_task_create(
            project=project,
            data={
                'assigned_to': project_member,
                'title': 'Implement CORS policy',
                'category': 'vulnerability_fix',
                'priority': 'high',
                'status': 'todo',
                'created_by_agent': 'PM Agent',
            },
        )

        list_response = self.client.get(
            reverse('api:projects:project-task-list', kwargs={'version': 'v1', 'project_id': project.id}),
            **self.auth_header(self.member),
        )
        detail_response = self.client.get(
            reverse(
                'api:projects:project-task-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'task_id': project_task.id},
            ),
            **self.auth_header(self.member),
        )
        public_create_response = self.client.post(
            reverse('api:projects:project-task-list', kwargs={'version': 'v1', 'project_id': project.id}),
            {'title': 'Should not be public'},
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        assigned_status_response = self.client.patch(
            reverse(
                'api:projects:project-task-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'task_id': project_task.id},
            ),
            {'status': 'in_progress'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        assigned_forbidden_response = self.client.patch(
            reverse(
                'api:projects:project-task-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'task_id': project_task.id},
            ),
            {'title': 'Nope'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        creator_update_response = self.client.patch(
            reverse(
                'api:projects:project-task-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'task_id': project_task.id},
            ),
            {'assigned_to_id': owner_membership.id, 'priority': 'critical', 'title': 'Finalize CORS policy'},
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        outsider_response = self.client.get(
            reverse(
                'api:projects:project-task-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'task_id': project_task.id},
            ),
            **self.auth_header(self.outsider),
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.json()['count'], 1)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(public_create_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(assigned_status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(assigned_status_response.json()['status'], 'in_progress')
        self.assertEqual(assigned_forbidden_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(creator_update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(creator_update_response.json()['priority'], 'critical')
        self.assertEqual(creator_update_response.json()['assigned_to_id'], owner_membership.id)
        self.assertEqual(outsider_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_mutations_are_auto_audited(self):
        project = self.create_project()
        project_member = ProjectMember.objects.create(
            project=project,
            user=self.member,
            invited_by=self.creator,
            display_role='Backend Developer',
            roles=['backend'],
        )
        owner_membership = ProjectMember.objects.get(project=project, user=self.creator)
        project_task = project_task_create(
            project=project,
            data={
                'assigned_to': project_member,
                'title': 'Review auth flow',
                'priority': 'medium',
                'status': 'todo',
                'created_by_agent': 'PM Agent',
            },
        )

        assigned_status_response = self.client.patch(
            reverse(
                'api:projects:project-task-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'task_id': project_task.id},
            ),
            {'status': 'in_progress'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        creator_update_response = self.client.patch(
            reverse(
                'api:projects:project-task-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'task_id': project_task.id},
            ),
            {
                'assigned_to_id': owner_membership.id,
                'priority': 'critical',
                'due_date': '2026-05-08',
                'title': 'Review and harden auth flow',
            },
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        delete_response = self.client.delete(
            reverse(
                'api:projects:project-task-detail',
                kwargs={'version': 'v1', 'project_id': project.id, 'task_id': project_task.id},
            ),
            **self.auth_header(self.creator),
        )
        list_response = self.client.get(
            reverse('api:projects:project-audit-log-list', kwargs={'version': 'v1', 'project_id': project.id}),
            **self.auth_header(self.member),
        )
        outsider_response = self.client.get(
            reverse('api:projects:project-audit-log-list', kwargs={'version': 'v1', 'project_id': project.id}),
            **self.auth_header(self.outsider),
        )

        self.assertEqual(assigned_status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(creator_update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectTask.objects.filter(id=project_task.id).exists())
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(outsider_response.status_code, status.HTTP_404_NOT_FOUND)

        events = set(ProjectAuditLog.objects.filter(project=project).values_list('event_type', flat=True))
        self.assertIn(ProjectAuditLog.EventType.TASK_CREATED, events)
        self.assertIn(ProjectAuditLog.EventType.TASK_STATUS_CHANGED, events)
        self.assertIn(ProjectAuditLog.EventType.TASK_REASSIGNED, events)
        self.assertIn(ProjectAuditLog.EventType.TASK_PRIORITY_CHANGED, events)
        self.assertIn(ProjectAuditLog.EventType.TASK_DUE_DATE_CHANGED, events)
        self.assertIn(ProjectAuditLog.EventType.TASK_UPDATED, events)
        self.assertIn(ProjectAuditLog.EventType.TASK_DELETED, events)

        created_log = ProjectAuditLog.objects.get(project=project, event_type=ProjectAuditLog.EventType.TASK_CREATED)
        status_log = ProjectAuditLog.objects.get(project=project, event_type=ProjectAuditLog.EventType.TASK_STATUS_CHANGED)
        priority_log = ProjectAuditLog.objects.get(project=project, event_type=ProjectAuditLog.EventType.TASK_PRIORITY_CHANGED)
        self.assertEqual(created_log.actor_agent, 'PM Agent')
        self.assertEqual(status_log.actor_user, self.member)
        self.assertEqual(priority_log.actor_user, self.creator)
        self.assertEqual(priority_log.before, {'priority': 'medium'})
        self.assertEqual(priority_log.after, {'priority': 'critical'})
        self.assertGreaterEqual(list_response.json()['count'], 7)

    def test_vulnerability_mark_resolved_is_auto_audited(self):
        project = self.create_project()
        vulnerability = project_vulnerability_create(
            project=project,
            data={'title': 'Missing authorization check', 'severity': 'critical', 'status': 'open'},
        )

        project_vulnerability_mark_resolved(vulnerability=vulnerability, actor_agent='SR Dev Agent')

        vulnerability.refresh_from_db()
        audit_log = ProjectAuditLog.objects.get(project=project, event_type=ProjectAuditLog.EventType.VULNERABILITY_RESOLVED)
        self.assertEqual(vulnerability.status, 'resolved')
        self.assertEqual(audit_log.actor_agent, 'SR Dev Agent')
        self.assertEqual(audit_log.target_type, ProjectAuditLog.TargetType.PROJECT_VULNERABILITY)
        self.assertEqual(audit_log.target_id, vulnerability.id)
        self.assertEqual(audit_log.before, {'status': 'open'})
        self.assertEqual(audit_log.after, {'status': 'resolved'})
