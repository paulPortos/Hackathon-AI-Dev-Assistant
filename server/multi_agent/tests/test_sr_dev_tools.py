import base64
import importlib
from unittest.mock import patch

from django.test import TestCase

from multi_agent.agents.sr_dev.tools import (
    sr_dev_compare_repository_refs,
    sr_dev_find_dependency_manifests,
    sr_dev_get_commit_status,
    sr_dev_get_context,
    sr_dev_list_repository_tree,
    sr_dev_prepare_pm_handoff,
    sr_dev_read_repository_file,
    sr_dev_search_repository_code,
)
from projects.models import Project, ProjectMember, ProjectTask, ProjectVulnerability
from user_descriptions.models import UserDescription
from users.models import User


sr_dev_read_repository_file_module = importlib.import_module('multi_agent.agents.sr_dev.tools.sr_dev_read_repository_file')
sr_dev_search_repository_code_module = importlib.import_module('multi_agent.agents.sr_dev.tools.sr_dev_search_repository_code')
sr_dev_list_repository_tree_module = importlib.import_module('multi_agent.agents.sr_dev.tools.sr_dev_list_repository_tree')
sr_dev_compare_repository_refs_module = importlib.import_module('multi_agent.agents.sr_dev.tools.sr_dev_compare_repository_refs')
sr_dev_get_commit_status_module = importlib.import_module('multi_agent.agents.sr_dev.tools.sr_dev_get_commit_status')
sr_dev_find_dependency_manifests_module = importlib.import_module('multi_agent.agents.sr_dev.tools.sr_dev_find_dependency_manifests')


class SrDevToolTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            github_id='1',
            username='creator',
            name='Creator',
            email='creator@example.com',
            access_token='creator-token',
        )
        self.member = User.objects.create_user(
            github_id='2',
            username='member',
            name='Member',
            email='member@example.com',
            access_token='member-token',
        )
        self.outsider = User.objects.create_user(
            github_id='3',
            username='outsider',
            name='Outsider',
            email='outsider@example.com',
            access_token='outsider-token',
        )
        self.project = Project.objects.create(
            creator=self.creator,
            github_repo_id=123,
            github_full_name='octocat/hello-world',
            github_html_url='https://github.com/octocat/hello-world',
            github_clone_url='https://github.com/octocat/hello-world.git',
            github_default_branch='main',
            github_visibility='public',
            github_primary_language='Python',
            github_languages={'Python': 1000},
            github_description='A test repository',
            overview='Backend security assistant',
            goals='Verify user claims against code',
            tech_stack=['Django', 'DRF'],
            business_context='Hackathon MVP',
            agent_notes='Be precise',
        )
        ProjectMember.objects.create(project=self.project, user=self.creator, invited_by=self.creator, display_role='Owner', roles=['owner'])
        self.member_record = ProjectMember.objects.create(
            project=self.project,
            user=self.member,
            invited_by=self.creator,
            display_role='Backend Developer',
            roles=['backend'],
        )
        UserDescription.objects.create(
            user=self.member,
            primary_role='backend',
            experience_level='mid',
            summary='Builds Django APIs',
            skills=[{'name': 'Django', 'level': 4}],
            preferred_tasks=['backend_api'],
            avoided_tasks=['frontend_ui'],
        )

    def encoded_file(self, content):
        return base64.b64encode(content.encode()).decode()

    def test_sr_dev_get_context_returns_project_and_current_user_role(self):
        payload = sr_dev_get_context(project_id=self.project.id, current_user_id=self.member.id)

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['project_context']['project']['github_full_name'], 'octocat/hello-world')
        self.assertEqual(payload['current_user']['username'], 'member')
        self.assertEqual(payload['current_user_description']['primary_role'], 'backend')
        self.assertEqual(payload['current_user_project_role']['display_role'], 'Backend Developer')

    def test_sr_dev_get_context_rejects_non_members(self):
        payload = sr_dev_get_context(project_id=self.project.id, current_user_id=self.outsider.id)

        self.assertFalse(payload['ok'])
        self.assertEqual(payload['code'], 'not_project_member')

    @patch.object(sr_dev_read_repository_file_module, 'fetch_github_repository_content')
    @patch.object(sr_dev_read_repository_file_module, 'github_access_token_get_valid')
    def test_sr_dev_read_repository_file_reads_selected_commit_with_creator_token(self, token_get_valid, fetch_content):
        token_get_valid.return_value = 'creator-token'
        fetch_content.return_value = {
            'type': 'file',
            'encoding': 'base64',
            'path': 'server/config/settings.py',
            'size': 25,
            'content': self.encoded_file('SECRET_KEY = "test"\n'),
        }

        payload = sr_dev_read_repository_file(
            project_id=self.project.id,
            current_user_id=self.member.id,
            commit_sha='abc123',
            path='server/config/settings.py',
        )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['commit_sha'], 'abc123')
        self.assertEqual(payload['content'], 'SECRET_KEY=[REDACTED]\n')
        self.assertTrue(payload['sensitive_content_redacted'])
        token_get_valid.assert_called_once_with(self.creator)
        fetch_content.assert_called_once_with(
            access_token='creator-token',
            repository='octocat/hello-world',
            path='server/config/settings.py',
            ref='abc123',
        )

    @patch.object(sr_dev_read_repository_file_module, 'fetch_github_repository_content')
    def test_sr_dev_read_repository_file_rejects_non_members_before_github_call(self, fetch_content):
        payload = sr_dev_read_repository_file(
            project_id=self.project.id,
            current_user_id=self.outsider.id,
            commit_sha='abc123',
            path='server/config/settings.py',
        )

        self.assertFalse(payload['ok'])
        self.assertEqual(payload['code'], 'not_project_member')
        fetch_content.assert_not_called()

    @patch.object(sr_dev_read_repository_file_module, 'fetch_github_repository_content')
    def test_sr_dev_read_repository_file_blocks_sensitive_paths_before_github_call(self, fetch_content):
        payload = sr_dev_read_repository_file(
            project_id=self.project.id,
            current_user_id=self.member.id,
            commit_sha='abc123',
            path='.env',
        )

        self.assertFalse(payload['ok'])
        self.assertEqual(payload['code'], 'sensitive_file_blocked')
        fetch_content.assert_not_called()

    @patch.object(sr_dev_search_repository_code_module, 'fetch_github_repository_content')
    @patch.object(sr_dev_search_repository_code_module, 'search_github_repository_code')
    @patch.object(sr_dev_search_repository_code_module, 'project_repository_branch_list')
    @patch.object(sr_dev_search_repository_code_module, 'github_access_token_get_valid')
    def test_sr_dev_search_repository_code_returns_snippets_only(self, token_get_valid, branch_list, search_code, fetch_content):
        token_get_valid.return_value = 'creator-token'
        branch_list.return_value = {
            'default_branch': 'main',
            'branches': [{'name': 'main', 'commit_sha': 'abc123', 'is_default': True}],
        }
        search_code.return_value = {'items': [{'path': 'server/auth.py'}]}
        fetch_content.return_value = {
            'type': 'file',
            'encoding': 'base64',
            'path': 'server/auth.py',
            'size': 120,
            'content': self.encoded_file('line one\nsafe auth middleware\nline three\nline four\n'),
        }

        payload = sr_dev_search_repository_code(
            project_id=self.project.id,
            current_user_id=self.member.id,
            commit_sha='abc123',
            query='auth middleware',
        )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['search_mode'], 'github_code_search')
        self.assertEqual(payload['result_count'], 1)
        self.assertEqual(payload['results'][0]['path'], 'server/auth.py')
        self.assertIn('safe auth middleware', payload['results'][0]['snippet'])
        self.assertNotIn('content', payload['results'][0])
        fetch_content.assert_called_once_with(
            access_token='creator-token',
            repository='octocat/hello-world',
            path='server/auth.py',
            ref='abc123',
        )

    @patch.object(sr_dev_search_repository_code_module, 'fetch_github_repository_content')
    @patch.object(sr_dev_search_repository_code_module, 'search_github_repository_code')
    @patch.object(sr_dev_search_repository_code_module, 'project_repository_branch_list')
    @patch.object(sr_dev_search_repository_code_module, 'github_access_token_get_valid')
    def test_sr_dev_search_repository_code_redacts_secret_like_snippets(self, token_get_valid, branch_list, search_code, fetch_content):
        token_get_valid.return_value = 'creator-token'
        branch_list.return_value = {
            'default_branch': 'main',
            'branches': [{'name': 'main', 'commit_sha': 'abc123', 'is_default': True}],
        }
        search_code.return_value = {'items': [{'path': 'server/config/settings.py'}]}
        fetch_content.return_value = {
            'type': 'file',
            'encoding': 'base64',
            'path': 'server/config/settings.py',
            'size': 120,
            'content': self.encoded_file('SECRET_KEY = "abc"\n'),
        }

        payload = sr_dev_search_repository_code(
            project_id=self.project.id,
            current_user_id=self.member.id,
            commit_sha='abc123',
            query='SECRET_KEY',
        )

        self.assertTrue(payload['ok'])
        self.assertTrue(payload['sensitive_content_redacted'])
        self.assertEqual(payload['results'][0]['snippet'], 'SECRET_KEY=[REDACTED]')

    @patch.object(sr_dev_search_repository_code_module, 'fetch_github_repository_content')
    @patch.object(sr_dev_search_repository_code_module, 'fetch_github_repository_tree')
    @patch.object(sr_dev_search_repository_code_module, 'project_repository_branch_list')
    @patch.object(sr_dev_search_repository_code_module, 'github_access_token_get_valid')
    def test_sr_dev_search_repository_code_uses_tree_scan_for_non_default_commit(self, token_get_valid, branch_list, fetch_tree, fetch_content):
        token_get_valid.return_value = 'creator-token'
        branch_list.return_value = {
            'default_branch': 'main',
            'branches': [{'name': 'main', 'commit_sha': 'main-sha', 'is_default': True}],
        }
        fetch_tree.return_value = {
            'tree': [
                {'path': 'server/auth.py', 'type': 'blob', 'size': 120},
                {'path': 'assets/logo.png', 'type': 'blob', 'size': 100},
            ]
        }
        fetch_content.return_value = {
            'type': 'file',
            'encoding': 'base64',
            'path': 'server/auth.py',
            'size': 120,
            'content': self.encoded_file('safe auth middleware\n'),
        }

        payload = sr_dev_search_repository_code(
            project_id=self.project.id,
            current_user_id=self.member.id,
            commit_sha='feature-sha',
            query='auth',
        )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['search_mode'], 'tree_scan')
        self.assertEqual(payload['result_count'], 1)
        fetch_tree.assert_called_once_with(
            access_token='creator-token',
            repository='octocat/hello-world',
            ref='feature-sha',
        )

    @patch.object(sr_dev_search_repository_code_module, 'fetch_github_repository_content')
    @patch.object(sr_dev_search_repository_code_module, 'fetch_github_repository_tree')
    @patch.object(sr_dev_search_repository_code_module, 'project_repository_branch_list')
    @patch.object(sr_dev_search_repository_code_module, 'github_access_token_get_valid')
    def test_sr_dev_search_repository_code_reports_truncation(self, token_get_valid, branch_list, fetch_tree, fetch_content):
        token_get_valid.return_value = 'creator-token'
        branch_list.return_value = {
            'default_branch': 'main',
            'branches': [{'name': 'main', 'commit_sha': 'main-sha', 'is_default': True}],
        }
        fetch_tree.return_value = {
            'tree': [
                {'path': f'server/file_{index}.py', 'type': 'blob', 'size': 20}
                for index in range(45)
            ]
        }
        fetch_content.return_value = {
            'type': 'file',
            'encoding': 'base64',
            'path': 'server/file.py',
            'size': 20,
            'content': self.encoded_file('no match here\n'),
        }

        payload = sr_dev_search_repository_code(
            project_id=self.project.id,
            current_user_id=self.member.id,
            commit_sha='feature-sha',
            query='missing',
        )

        self.assertTrue(payload['ok'])
        self.assertTrue(payload['truncated'])
        self.assertEqual(payload['truncation_code'], 'search_truncated')
        self.assertEqual(payload['scanned_files'], 40)

    @patch.object(sr_dev_list_repository_tree_module, 'fetch_github_repository_tree')
    @patch.object(sr_dev_list_repository_tree_module, 'sr_dev_repository_context_resolve')
    def test_sr_dev_list_repository_tree_filters_sensitive_paths(self, context_resolve, fetch_tree):
        context_resolve.return_value = (self.project, 'creator-token', None)
        fetch_tree.return_value = {
            'tree': [
                {'path': '.env', 'type': 'blob', 'size': 20},
                {'path': 'server/config/settings.py', 'type': 'blob', 'size': 120},
            ]
        }

        payload = sr_dev_list_repository_tree(
            project_id=self.project.id,
            current_user_id=self.member.id,
            commit_sha='abc123',
        )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['result_count'], 1)
        self.assertEqual(payload['entries'][0]['path'], 'server/config/settings.py')
        self.assertEqual(payload['skipped_sensitive_files'], 1)

    @patch.object(sr_dev_compare_repository_refs_module, 'fetch_github_repository_compare')
    @patch.object(sr_dev_compare_repository_refs_module, 'sr_dev_repository_context_resolve')
    def test_sr_dev_compare_repository_refs_returns_compact_metadata(self, context_resolve, fetch_compare):
        context_resolve.return_value = (self.project, 'creator-token', None)
        fetch_compare.return_value = {
            'status': 'ahead',
            'ahead_by': 2,
            'behind_by': 0,
            'total_commits': 1,
            'commits': [{'sha': 'abc123', 'commit': {'message': 'Add auth\n\nbody', 'author': {'date': '2026-05-06T00:00:00Z'}}}],
            'files': [{'filename': 'server/auth.py', 'status': 'modified', 'additions': 5, 'deletions': 1, 'changes': 6}],
        }

        payload = sr_dev_compare_repository_refs(
            project_id=self.project.id,
            current_user_id=self.member.id,
            base_ref='main',
            head_ref='feature/auth',
        )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['files'][0]['filename'], 'server/auth.py')
        self.assertEqual(payload['commits'][0]['message'], 'Add auth')

    @patch.object(sr_dev_get_commit_status_module, 'fetch_github_repository_commit_status')
    @patch.object(sr_dev_get_commit_status_module, 'sr_dev_repository_context_resolve')
    def test_sr_dev_get_commit_status_returns_combined_status(self, context_resolve, fetch_status):
        context_resolve.return_value = (self.project, 'creator-token', None)
        fetch_status.return_value = {
            'sha': 'abc123',
            'state': 'success',
            'total_count': 1,
            'statuses': [{'context': 'ci', 'state': 'success', 'description': 'Passed', 'target_url': 'https://ci.example.com'}],
        }

        payload = sr_dev_get_commit_status(
            project_id=self.project.id,
            current_user_id=self.member.id,
            reference='abc123',
        )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['state'], 'success')
        self.assertEqual(payload['statuses'][0]['context'], 'ci')

    @patch.object(sr_dev_find_dependency_manifests_module, 'fetch_github_repository_tree')
    @patch.object(sr_dev_find_dependency_manifests_module, 'sr_dev_repository_context_resolve')
    def test_sr_dev_find_dependency_manifests_returns_known_manifests(self, context_resolve, fetch_tree):
        context_resolve.return_value = (self.project, 'creator-token', None)
        fetch_tree.return_value = {
            'tree': [
                {'path': 'package.json', 'type': 'blob', 'size': 120},
                {'path': 'server/requirements.txt', 'type': 'blob', 'size': 80},
                {'path': 'server/app.py', 'type': 'blob', 'size': 50},
            ]
        }

        payload = sr_dev_find_dependency_manifests(
            project_id=self.project.id,
            current_user_id=self.member.id,
            commit_sha='abc123',
        )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['manifest_count'], 2)
        self.assertEqual({item['filename'] for item in payload['manifests']}, {'package.json', 'requirements.txt'})

    def test_sr_dev_prepare_pm_handoff_returns_json_without_writing_records(self):
        payload = sr_dev_prepare_pm_handoff(
            project_id=self.project.id,
            current_user_id=self.member.id,
            conversation_summary='Auth review found one issue.',
            findings=[{'title': 'Missing CSRF review', 'severity': 'medium'}],
        )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['handoff_version'], 'sr_dev_to_pm.v1')
        self.assertTrue(payload['handoff_id'])
        self.assertEqual(payload['source_agent'], 'sr_dev')
        self.assertEqual(payload['project']['id'], self.project.id)
        self.assertNotIn('recommended_tasks', payload)
        self.assertEqual(ProjectTask.objects.count(), 0)
        self.assertEqual(ProjectVulnerability.objects.count(), 0)
