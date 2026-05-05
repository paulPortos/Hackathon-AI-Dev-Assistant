from importlib import import_module
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from multi_agent.agents.pm import project_manager_agent_process_handoff
from multi_agent.agents.sr_dev.tools import sr_dev_prepare_pm_handoff
from multi_agent.models import ProjectManagerAgentRun, SeniorDevMessage, SeniorDevSession, SeniorDevToolCall
from projects.models import Project, ProjectAuditLog, ProjectMember, ProjectTask, ProjectVulnerability
from user_descriptions.models import UserDescription
from users.models import User


pm_workflow_module = import_module('multi_agent.agents.pm.workflows.project_manager_agent_process_handoff')


class ProjectManagerAgentTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            github_id='301',
            username='creator',
            name='Creator',
            email='creator@example.com',
        )
        self.backend = User.objects.create_user(
            github_id='302',
            username='backend',
            name='Backend Dev',
            email='backend@example.com',
        )
        self.outsider = User.objects.create_user(
            github_id='303',
            username='outsider',
            name='Outsider',
            email='outsider@example.com',
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
            overview='Security review project',
            goals='Ship safer auth',
            tech_stack=['Django', 'DRF'],
            business_context='Hackathon MVP',
            agent_notes='Favor security fixes first',
        )
        ProjectMember.objects.create(
            project=self.project,
            user=self.creator,
            invited_by=self.creator,
            display_role='Owner',
            roles=['owner', 'architect'],
        )
        self.backend_member = ProjectMember.objects.create(
            project=self.project,
            user=self.backend,
            invited_by=self.creator,
            display_role='Backend Security Engineer',
            roles=['backend', 'security'],
        )
        UserDescription.objects.create(
            user=self.backend,
            primary_role='backend',
            experience_level='senior',
            summary='Builds secure Django APIs and auth flows.',
            skills=[{'name': 'Django', 'level': 5}, {'name': 'security', 'level': 4}],
            preferred_tasks=['vulnerability_fix', 'feature'],
            availability_notes='Available weekdays',
        )

    def build_sr_dev_source(self, *, findings=None, tool_results=None):
        session = SeniorDevSession.objects.create(
            project=self.project,
            user=self.backend,
            commit_sha='abc123',
            branch_name='main',
        )
        user_message = SeniorDevMessage.objects.create(
            session=session,
            role=SeniorDevMessage.Role.USER,
            text_content='Please verify auth safety.',
        )
        for tool_result in tool_results or []:
            SeniorDevToolCall.objects.create(
                session=session,
                message=user_message,
                tool_name=tool_result.get('tool_name', 'search_code'),
                safe_input_summary=tool_result.get('safe_input_summary', {}),
                safe_result_summary=tool_result.get('safe_result_summary', {}),
                status=SeniorDevToolCall.Status.SUCCESS,
                duration_ms=10,
                commit_sha=tool_result.get('commit_sha', 'abc123'),
            )
        handoff = sr_dev_prepare_pm_handoff(
            project_id=self.project.id,
            current_user_id=self.backend.id,
            conversation_summary='Sr Dev found auth risk.',
            findings=findings or [],
        )
        assistant_message = SeniorDevMessage.objects.create(
            session=session,
            source_user_message=user_message,
            role=SeniorDevMessage.Role.ASSISTANT,
            text_content='I found one issue.',
            structured_payload={'handoff': handoff},
        )
        return assistant_message, handoff

    def code_tool_result(self, path='server/config/settings.py', line_number=12, snippet='TOKEN = "abc"'):
        return {
            'tool_name': 'search_code',
            'safe_result_summary': {
                'ok': True,
                'query': 'TOKEN',
                'result_count': 1,
                'results': [{'path': path, 'line_number': line_number, 'snippet': snippet}],
            },
        }

    def test_pm_agent_creates_records_assigns_member_and_stores_run(self):
        evidence = [
            {
                'type': 'code',
                'summary': 'Token-like setting in config',
                'path': 'server/config/settings.py',
                'start_line': 12,
                'snippet': 'TOKEN = "abc"',
            }
        ]
        assistant_message, handoff = self.build_sr_dev_source(
            findings=[
                {
                    'title': 'Hardcoded token',
                    'summary': 'A token-like value appears in settings.',
                    'severity': 'critical',
                    'category': 'security',
                    'affected_path': 'server/config/settings.py',
                    'confidence_score': 91,
                    'confidence_reason': 'Code search found a token-like value.',
                    'evidence': evidence,
                }
            ],
            tool_results=[self.code_tool_result()],
        )
        agent_output = {
            'summary': 'Create one vulnerability and one fix task.',
            'vulnerabilities': [
                {
                    'source_finding_index': 0,
                    'title': 'Hardcoded token',
                    'severity': 'critical',
                    'confidence_score': 10,
                    'confidence_reason': 'PM output should not override Sr Dev confidence.',
                }
            ],
            'tasks': [
                {
                    'source_finding_index': 0,
                    'source_item_id': 'remove-hardcoded-token',
                    'title': 'Remove hardcoded token',
                    'description': 'Move token into env vars.',
                    'category': 'vulnerability_fix',
                    'priority': 'critical',
                    'confidence_score': 5,
                    'confidence_reason': 'PM output should not override Sr Dev confidence.',
                    'related_finding_index': 0,
                }
            ],
        }

        with patch.object(pm_workflow_module, 'project_manager_agent_run', return_value=agent_output):
            payload = project_manager_agent_process_handoff(self.project.id, self.backend.id, assistant_message.id)

        task = ProjectTask.objects.get(title='Remove hardcoded token')
        vulnerability = ProjectVulnerability.objects.get(title='Hardcoded token')

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['status'], ProjectManagerAgentRun.Status.COMPLETED)
        self.assertEqual(payload['created_vulnerabilities'][0]['id'], vulnerability.id)
        self.assertEqual(payload['created_tasks'][0]['id'], task.id)
        self.assertEqual(task.assigned_to_id, self.backend_member.id)
        self.assertEqual(task.related_finding_id, vulnerability.id)
        self.assertEqual(task.confidence_score, 91)
        self.assertEqual(task.confidence_reason, 'Code search found a token-like value.')
        self.assertEqual(task.evidence[0]['path'], 'server/config/settings.py')
        self.assertEqual(vulnerability.confidence_score, 91)
        self.assertEqual(vulnerability.confidence_reason, 'Code search found a token-like value.')
        self.assertEqual(ProjectManagerAgentRun.objects.get().handoff_id, handoff['handoff_id'])
        self.assertTrue(ProjectAuditLog.objects.filter(project=self.project, event_type=ProjectAuditLog.EventType.VULNERABILITY_CREATED).exists())

    def test_pm_agent_duplicate_handoff_returns_existing_run_without_duplicate_records(self):
        evidence = [{'type': 'code', 'path': 'server/config/settings.py', 'start_line': 12, 'snippet': 'TOKEN = "abc"'}]
        assistant_message, _handoff = self.build_sr_dev_source(
            findings=[{'title': 'Hardcoded token', 'severity': 'high', 'confidence_score': 88, 'confidence_reason': 'Sr Dev verified code evidence.', 'evidence': evidence}],
            tool_results=[self.code_tool_result()],
        )
        agent_output = {
            'summary': 'Create records.',
            'vulnerabilities': [{'source_finding_index': 0, 'title': 'Hardcoded token', 'severity': 'high'}],
            'tasks': [{'source_finding_index': 0, 'source_item_id': 'remove-token', 'title': 'Remove token', 'category': 'vulnerability_fix'}],
        }

        with patch.object(pm_workflow_module, 'project_manager_agent_run', return_value=agent_output) as agent_run:
            first_payload = project_manager_agent_process_handoff(self.project.id, self.backend.id, assistant_message.id)
            second_payload = project_manager_agent_process_handoff(self.project.id, self.backend.id, assistant_message.id)

        self.assertTrue(first_payload['ok'])
        self.assertTrue(second_payload['ok'])
        self.assertFalse(first_payload['idempotent_replay'])
        self.assertTrue(second_payload['idempotent_replay'])
        self.assertEqual(ProjectManagerAgentRun.objects.count(), 1)
        self.assertEqual(ProjectVulnerability.objects.count(), 1)
        self.assertEqual(ProjectTask.objects.count(), 1)
        agent_run.assert_called_once()

    def test_pm_agent_skips_low_confidence_items(self):
        evidence = [{'type': 'code', 'path': 'server/config/settings.py', 'start_line': 12, 'snippet': 'TOKEN = "abc"'}]
        assistant_message, _handoff = self.build_sr_dev_source(
            findings=[{'title': 'Maybe token', 'severity': 'medium', 'confidence_score': 55, 'evidence': evidence}],
            tool_results=[self.code_tool_result()],
        )
        agent_output = {
            'summary': 'Reject weak items.',
            'vulnerabilities': [{'source_finding_index': 0, 'title': 'Maybe token'}],
            'tasks': [{'source_finding_index': 0, 'title': 'Investigate token', 'category': 'vulnerability_fix'}],
        }

        with patch.object(pm_workflow_module, 'project_manager_agent_run', return_value=agent_output):
            payload = project_manager_agent_process_handoff(self.project.id, self.backend.id, assistant_message.id)

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['status'], ProjectManagerAgentRun.Status.REJECTED)
        self.assertEqual(ProjectVulnerability.objects.count(), 0)
        self.assertEqual(ProjectTask.objects.count(), 0)
        self.assertEqual({item['code'] for item in payload['rejected_items']}, {'low_confidence'})

    def test_pm_agent_rejects_vulnerability_without_matching_tool_proof(self):
        evidence = [{'type': 'code', 'path': 'auth/views.py', 'start_line': 42, 'snippet': 'no throttle'}]
        assistant_message, _handoff = self.build_sr_dev_source(
            findings=[{'title': 'Missing throttling', 'severity': 'high', 'confidence_score': 90, 'evidence': evidence}],
            tool_results=[self.code_tool_result(path='server/config/settings.py')],
        )
        agent_output = {
            'summary': 'Reject unmatched proof.',
            'vulnerabilities': [{'source_finding_index': 0, 'title': 'Missing throttling', 'severity': 'high'}],
            'tasks': [],
        }

        with patch.object(pm_workflow_module, 'project_manager_agent_run', return_value=agent_output):
            payload = project_manager_agent_process_handoff(self.project.id, self.backend.id, assistant_message.id)

        self.assertTrue(payload['ok'])
        self.assertEqual(ProjectVulnerability.objects.count(), 0)
        self.assertEqual(payload['rejected_items'][0]['code'], 'insufficient_tool_proof')

    def test_conversation_evidence_can_create_non_vulnerability_task_only(self):
        conversation_evidence = [{'type': 'conversation', 'summary': 'User asked for onboarding checklist.'}]
        assistant_message, _handoff = self.build_sr_dev_source(
            findings=[{'title': 'Conversation-only vulnerability', 'severity': 'high', 'confidence_score': 90, 'evidence': conversation_evidence}],
            tool_results=[{'tool_name': 'get_context', 'safe_result_summary': {'ok': True, 'project_id': self.project.id}}],
        )
        agent_output = {
            'summary': 'Create feature task only.',
            'vulnerabilities': [{'source_finding_index': 0, 'title': 'Conversation-only vulnerability', 'severity': 'high'}],
            'tasks': [{'source_finding_index': 0, 'title': 'Create onboarding checklist', 'category': 'feature'}],
        }

        with patch.object(pm_workflow_module, 'project_manager_agent_run', return_value=agent_output):
            payload = project_manager_agent_process_handoff(self.project.id, self.backend.id, assistant_message.id)

        self.assertTrue(payload['ok'])
        self.assertEqual(ProjectVulnerability.objects.count(), 0)
        self.assertEqual(ProjectTask.objects.count(), 1)
        self.assertEqual(payload['rejected_items'][0]['code'], 'insufficient_tool_proof')

    def test_pm_agent_returns_stable_errors_for_invalid_inputs(self):
        assistant_message, handoff = self.build_sr_dev_source(
            findings=[],
            tool_results=[self.code_tool_result()],
        )
        mismatched_handoff = {**handoff, 'project': {'id': self.project.id + 100}}

        outsider_payload = project_manager_agent_process_handoff(self.project.id, self.outsider.id, assistant_message.id, handoff)
        mismatch_payload = project_manager_agent_process_handoff(self.project.id, self.backend.id, assistant_message.id, mismatched_handoff)
        missing_source_message = SeniorDevMessage.objects.create(
            session=assistant_message.session,
            role=SeniorDevMessage.Role.ASSISTANT,
            text_content='No source link',
            structured_payload={'handoff': handoff},
        )
        missing_source_payload = project_manager_agent_process_handoff(self.project.id, self.backend.id, missing_source_message.id)

        self.assertFalse(outsider_payload['ok'])
        self.assertEqual(outsider_payload['code'], 'not_project_member')
        self.assertFalse(mismatch_payload['ok'])
        self.assertEqual(mismatch_payload['code'], 'project_mismatch')
        self.assertFalse(missing_source_payload['ok'])
        self.assertEqual(missing_source_payload['code'], 'missing_source_message')

    def test_agent_centric_package_structure_exists(self):
        base_path = Path(__file__).resolve().parents[1] / 'agents'

        self.assertTrue((base_path / 'sr_dev' / 'prompts').is_dir())
        self.assertTrue((base_path / 'pm' / 'workflows' / 'project_manager_agent_process_handoff.py').is_file())
        self.assertTrue((base_path / 'scrum' / 'workflows').is_dir())
