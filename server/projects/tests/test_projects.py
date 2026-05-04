import importlib
from datetime import datetime, time
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from projects.models import Project, ProjectMeetingSettings, ProjectMember, ProjectTask
from projects.selectors import project_get_agent_context, project_meeting_settings_due_for_reminder
from projects.services import project_meeting_reminder_send, project_task_create, project_vulnerability_create
from user_descriptions.models import UserDescription
from users.models import User


project_import_service_module = importlib.import_module('projects.services.project_import_from_github')
project_meeting_reminder_send_service_module = importlib.import_module('projects.services.project_meeting_reminder_send')


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

    def test_meeting_settings_are_one_per_project_and_creator_managed(self):
        project = self.create_project()
        ProjectMember.objects.create(project=project, user=self.member, invited_by=self.creator, display_role='Backend Developer', roles=['backend'])

        create_response = self.client.put(
            reverse('api:projects:project-meeting-settings-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            {
                'meeting_days': ['Monday', 'wednesday', 'monday'],
                'meeting_time': '09:30:00',
                'timezone': 'Asia/Manila',
                'google_meet_link': 'https://meet.google.com/abc-defg-hij',
                'weekly_goals': 'Ship project tasks.',
                'monthly_goals': 'Improve security posture.',
                'alert_minutes_before': 30,
                'is_active': True,
            },
            content_type='application/json',
            **self.auth_header(self.creator),
        )
        member_read_response = self.client.get(
            reverse('api:projects:project-meeting-settings-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            **self.auth_header(self.member),
        )
        forbidden_response = self.client.patch(
            reverse('api:projects:project-meeting-settings-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            {'weekly_goals': 'Not allowed'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        creator_update_response = self.client.patch(
            reverse('api:projects:project-meeting-settings-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            {'weekly_goals': 'Close all critical tasks.'},
            content_type='application/json',
            **self.auth_header(self.creator),
        )

        self.assertEqual(create_response.status_code, status.HTTP_200_OK)
        self.assertEqual(create_response.json()['meeting_days'], ['monday', 'wednesday'])
        self.assertEqual(member_read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(creator_update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(creator_update_response.json()['weekly_goals'], 'Close all critical tasks.')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProjectMeetingSettings.objects.create(
                    project=project,
                    meeting_days=['friday'],
                    meeting_time=time(10, 0),
                    timezone='Asia/Manila',
                    google_meet_link='https://meet.google.com/xyz-abcd-efg',
                )

    def test_due_reminder_selector_respects_schedule_and_last_sent_at(self):
        project = self.create_project()
        meeting_settings = ProjectMeetingSettings.objects.create(
            project=project,
            meeting_days=['monday'],
            meeting_time=time(10, 0),
            timezone='Asia/Manila',
            google_meet_link='https://meet.google.com/abc-defg-hij',
            alert_minutes_before=30,
        )
        current_datetime = datetime(2026, 5, 4, 1, 30, tzinfo=ZoneInfo('UTC'))

        due_settings = project_meeting_settings_due_for_reminder(current_datetime=current_datetime)
        meeting_settings.last_reminder_sent_at = current_datetime
        meeting_settings.save(update_fields=['last_reminder_sent_at', 'updated_at'])
        already_sent_settings = project_meeting_settings_due_for_reminder(current_datetime=current_datetime)

        self.assertEqual(due_settings, [meeting_settings])
        self.assertEqual(already_sent_settings, [])

    def test_scrum_reminder_email_composition_and_sendgrid_provider_are_mocked(self):
        project = self.create_project()
        project_member = ProjectMember.objects.create(
            project=project,
            user=self.member,
            invited_by=self.creator,
            display_role='Backend Developer',
            roles=['backend'],
        )
        meeting_settings = ProjectMeetingSettings.objects.create(
            project=project,
            meeting_days=['monday'],
            meeting_time=time(10, 0),
            timezone='Asia/Manila',
            google_meet_link='https://meet.google.com/abc-defg-hij',
            weekly_goals='Ship the auth hardening sprint.',
            monthly_goals='Reduce security risk.',
            alert_minutes_before=30,
        )
        project_task_create(
            project=project,
            data={
                'assigned_to': project_member,
                'title': 'Fix CORS configuration',
                'status': ProjectTask.Status.BLOCKED,
                'priority': ProjectTask.Priority.HIGH,
            },
        )
        project_task_create(
            project=project,
            data={'title': 'Document threat model', 'status': ProjectTask.Status.COMPLETED},
        )
        project_vulnerability_create(project=project, data={'title': 'Leaked token risk', 'severity': 'critical'})

        with patch.object(project_meeting_reminder_send_service_module, 'send_scrum_meeting_email') as send_email:
            project_meeting_reminder_send(
                meeting_settings=meeting_settings,
                current_datetime=datetime(2026, 5, 4, 1, 30, tzinfo=ZoneInfo('UTC')),
            )

        _, kwargs = send_email.call_args
        self.assertEqual(kwargs['to_emails'], ['creator@example.com', 'backend@example.com'])
        self.assertIn('https://meet.google.com/abc-defg-hij', kwargs['text_content'])
        self.assertIn('Ship the auth hardening sprint.', kwargs['text_content'])
        self.assertIn('Fix CORS configuration', kwargs['text_content'])
        self.assertIn('Leaked token risk', kwargs['text_content'])
        self.assertIn('Document threat model', kwargs['text_content'])
        meeting_settings.refresh_from_db()
        self.assertIsNotNone(meeting_settings.last_reminder_sent_at)
