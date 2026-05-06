import importlib
import inspect
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from multi_agent.agents.sr_dev.tools import senior_dev_scoped_tools_create
from multi_agent.models import SeniorDevClaim, SeniorDevFinding, SeniorDevMessage, SeniorDevSession, SeniorDevToolCall
from projects.models import Project, ProjectMember, ProjectTask, ProjectVulnerability
from users.models import User


senior_dev_message_process_module = importlib.import_module('multi_agent.agents.sr_dev.workflows.senior_dev_message_process')
senior_dev_agent_run_module = importlib.import_module('multi_agent.agents.sr_dev.agno.senior_dev_agent_run')
senior_dev_scoped_tools_create_module = importlib.import_module('multi_agent.agents.sr_dev.tools.senior_dev_scoped_tools_create')
senior_dev_memory_module = importlib.import_module('multi_agent.agents.sr_dev.prompts.senior_dev_session_memory_context_build')


class SeniorDevAgentTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            github_id='201',
            username='creator',
            name='Creator',
            email='creator@example.com',
            access_token='creator-token',
        )
        self.member = User.objects.create_user(
            github_id='202',
            username='member',
            name='Member',
            email='member@example.com',
            access_token='member-token',
        )
        self.outsider = User.objects.create_user(
            github_id='203',
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
        )
        ProjectMember.objects.create(project=self.project, user=self.creator, invited_by=self.creator, display_role='Owner', roles=['owner'])
        ProjectMember.objects.create(project=self.project, user=self.member, invited_by=self.creator, display_role='Backend Developer', roles=['backend'])

    def auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}

    def create_session(self, user=None):
        return SeniorDevSession.objects.create(
            project=self.project,
            user=user or self.member,
            commit_sha='abc123',
            branch_name='main',
        )

    def create_tool_proof_for_message(self, session, message, path='auth/views.py', line_number=42, snippet='Login view has no rate limit'):
        SeniorDevToolCall.objects.create(
            session=session,
            message=message,
            tool_name='get_context',
            safe_input_summary={},
            safe_result_summary={'ok': True, 'project_id': self.project.id},
            status=SeniorDevToolCall.Status.SUCCESS,
            duration_ms=5,
            commit_sha=session.commit_sha,
        )
        SeniorDevToolCall.objects.create(
            session=session,
            message=message,
            tool_name='search_code',
            safe_input_summary={'query': 'rate limit'},
            safe_result_summary={
                'ok': True,
                'results': [{'path': path, 'line_number': line_number, 'snippet': snippet}],
            },
            status=SeniorDevToolCall.Status.SUCCESS,
            duration_ms=5,
            commit_sha=session.commit_sha,
        )

    def test_session_create_requires_membership_and_commit_sha(self):
        success_response = self.client.post(
            reverse('api:agents:senior-dev-session-list', kwargs={'version': 'v1'}),
            {'project_id': self.project.id, 'commit_sha': 'abc123', 'branch_name': 'main'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        missing_commit_response = self.client.post(
            reverse('api:agents:senior-dev-session-list', kwargs={'version': 'v1'}),
            {'project_id': self.project.id, 'commit_sha': ''},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        outsider_response = self.client.post(
            reverse('api:agents:senior-dev-session-list', kwargs={'version': 'v1'}),
            {'project_id': self.project.id, 'commit_sha': 'abc123'},
            content_type='application/json',
            **self.auth_header(self.outsider),
        )

        self.assertEqual(success_response.status_code, status.HTTP_200_OK)
        self.assertEqual(success_response.json()['commit_sha'], 'abc123')
        self.assertEqual(missing_commit_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(outsider_response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(SR_DEV_AGENT_MODEL='gpt-oss:20b', OLLAMA_HOST='https://ollama.example', OLLAMA_API_KEY='test-token')
    @patch.object(senior_dev_agent_run_module, 'senior_dev_session_memory_context_build', return_value='No prior turns.')
    @patch.object(senior_dev_agent_run_module, 'Agent')
    @patch.object(senior_dev_agent_run_module, 'Ollama')
    def test_senior_dev_agent_uses_configured_ollama_model(self, ollama, agent_class, memory_build):
        session = self.create_session()
        user_message = SeniorDevMessage.objects.create(
            session=session,
            role=SeniorDevMessage.Role.USER,
            text_content='Check auth',
        )
        agent_class.return_value.run.return_value = SimpleNamespace(content='Done')

        result = senior_dev_agent_run_module.senior_dev_agent_run(
            session=session,
            user_message=user_message,
            tools=[],
        )

        self.assertEqual(result, 'Done')
        ollama.assert_called_once_with(
            id='gpt-oss:20b',
            host='https://ollama.example',
            api_key='test-token',
        )
        memory_build.assert_called_once_with(session=session, before_message=user_message)

    @override_settings(
        SR_DEV_AGENT_MODEL='gpt-oss:20b',
        OLLAMA_HOST='https://ollama.example',
        OLLAMA_API_KEY='test-token',
        OLLAMA_AGENT_MAX_ATTEMPTS=2,
        OLLAMA_AGENT_RETRY_DELAY_SECONDS=0,
    )
    @patch.object(senior_dev_agent_run_module, 'senior_dev_session_memory_context_build', return_value='No prior turns.')
    @patch.object(senior_dev_agent_run_module, 'Agent')
    @patch.object(senior_dev_agent_run_module, 'Ollama')
    def test_senior_dev_agent_retries_transient_ollama_provider_failure(self, ollama, agent_class, memory_build):
        session = self.create_session()
        user_message = SeniorDevMessage.objects.create(
            session=session,
            role=SeniorDevMessage.Role.USER,
            text_content='Check pagination',
        )
        agent_class.return_value.run.side_effect = [
            RuntimeError('Internal Server Error (status code: 500)'),
            SimpleNamespace(content='Retry succeeded'),
        ]

        result = senior_dev_agent_run_module.senior_dev_agent_run(
            session=session,
            user_message=user_message,
            tools=[],
        )

        self.assertEqual(result, 'Retry succeeded')
        self.assertEqual(agent_class.return_value.run.call_count, 2)

    def test_sessions_and_messages_are_member_scoped_and_paginated(self):
        session = self.create_session()
        SeniorDevMessage.objects.create(session=session, role=SeniorDevMessage.Role.USER, text_content='Hello')

        session_list_response = self.client.get(
            reverse('api:agents:senior-dev-session-list', kwargs={'version': 'v1'}),
            **self.auth_header(self.member),
        )
        detail_response = self.client.get(
            reverse('api:agents:senior-dev-session-detail', kwargs={'version': 'v1', 'session_id': session.id}),
            **self.auth_header(self.member),
        )
        messages_response = self.client.get(
            reverse('api:agents:senior-dev-message-list', kwargs={'version': 'v1', 'session_id': session.id}),
            **self.auth_header(self.member),
        )
        outsider_response = self.client.get(
            reverse('api:agents:senior-dev-session-detail', kwargs={'version': 'v1', 'session_id': session.id}),
            **self.auth_header(self.outsider),
        )

        self.assertEqual(session_list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(session_list_response.json()['count'], 1)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(messages_response.status_code, status.HTTP_200_OK)
        self.assertEqual(messages_response.json()['count'], 1)
        self.assertEqual(outsider_response.status_code, status.HTTP_404_NOT_FOUND)

    @patch.object(senior_dev_message_process_module, 'project_manager_agent_process_handoff')
    @patch.object(senior_dev_message_process_module, 'senior_dev_parser_run')
    @patch.object(senior_dev_message_process_module, 'senior_dev_agent_run')
    def test_text_message_flow_stores_claims_findings_and_runs_pm_handoff(self, agent_run, parser_run, pm_handoff):
        session = self.create_session()
        agent_run.side_effect = lambda *, session, user_message, tools: (
            self.create_tool_proof_for_message(session, user_message)
            or 'I checked the login endpoint and rate limiting appears missing.'
        )
        pm_handoff.return_value = {'ok': True, 'status': 'completed', 'created_tasks': [], 'created_vulnerabilities': []}
        parser_run.return_value = {
            'assistant_message': 'I checked the login endpoint and rate limiting appears missing.',
            'check_in_question': 'Do you want me to review authentication middleware next?',
            'choices': ['Yes', 'No'],
            'allow_free_text': True,
            'conversation_summary': 'Rate limit review.',
            'claims': [{'text': 'Login endpoint exists', 'category': 'auth', 'status': 'verified'}],
            'findings': [
                {
                    'type': 'vulnerability',
                    'title': 'Missing rate limiting on login endpoint',
                    'category': 'security',
                    'severity': 'high',
                    'confidence_score': 85,
                    'confidence_reason': 'No throttling tool evidence was present.',
                    'evidence': [{'type': 'code', 'summary': 'Login view has no rate limit', 'path': 'auth/views.py', 'start_line': 42}],
                }
            ],
        }

        response = self.client.post(
            reverse('api:agents:senior-dev-message-list', kwargs={'version': 'v1', 'session_id': session.id}),
            {'input_type': 'text', 'text': 'We already handle login safely.'},
            content_type='application/json',
            **self.auth_header(self.member),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['assistant_message'], 'I checked the login endpoint and rate limiting appears missing.')
        self.assertEqual(payload['check_in_question'], 'Do you want me to review authentication middleware next?')
        self.assertEqual(payload['claims'][0]['text'], 'Login endpoint exists')
        self.assertEqual(payload['findings'][0]['confidence_score'], 85)
        self.assertTrue(payload['handoff']['handoff_id'])
        self.assertTrue(payload['pm_handoff_result']['ok'])
        self.assertNotIn('recommended_tasks', payload['handoff'])
        self.assertEqual(SeniorDevClaim.objects.count(), 1)
        self.assertEqual(SeniorDevFinding.objects.count(), 1)
        self.assertEqual(SeniorDevFinding.objects.get().status, SeniorDevFinding.Status.HANDED_OFF)
        self.assertEqual(ProjectTask.objects.count(), 0)
        self.assertEqual(ProjectVulnerability.objects.count(), 0)
        pm_handoff.assert_called_once_with(self.project.id, self.member.id, payload['assistant_message_id'])

    @patch.object(senior_dev_message_process_module, 'senior_dev_parser_run')
    @patch.object(senior_dev_message_process_module, 'senior_dev_agent_run')
    def test_choice_and_open_text_messages_are_accepted(self, agent_run, parser_run):
        session = self.create_session()
        agent_run.return_value = 'Thanks, I will verify that claim.'
        parser_run.return_value = {
            'assistant_message': 'Thanks, I will verify that claim.',
            'check_in_question': '',
            'choices': [],
            'allow_free_text': True,
            'claims': [],
            'findings': [],
        }

        choice_response = self.client.post(
            reverse('api:agents:senior-dev-message-list', kwargs={'version': 'v1', 'session_id': session.id}),
            {'input_type': 'choice', 'choice': 'Review backend auth', 'choice_payload': {'id': 'backend-auth'}},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        open_text_response = self.client.post(
            reverse('api:agents:senior-dev-message-list', kwargs={'version': 'v1', 'session_id': session.id}),
            {'input_type': 'open_text', 'text': 'Please also inspect middleware.'},
            content_type='application/json',
            **self.auth_header(self.member),
        )

        self.assertEqual(choice_response.status_code, status.HTTP_200_OK)
        self.assertEqual(open_text_response.status_code, status.HTTP_200_OK)
        self.assertEqual(SeniorDevMessage.objects.filter(role=SeniorDevMessage.Role.USER).count(), 2)

    @patch.object(senior_dev_message_process_module, 'senior_dev_parser_run')
    @patch.object(senior_dev_message_process_module, 'senior_dev_agent_run')
    def test_audio_message_is_rejected_by_ollama_only_stack(self, agent_run, parser_run):
        session = self.create_session()

        response = self.client.post(
            reverse('api:agents:senior-dev-message-list', kwargs={'version': 'v1', 'session_id': session.id}),
            {'input_type': 'audio'},
            content_type='application/json',
            **self.auth_header(self.member),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('input_type', response.json())
        self.assertEqual(SeniorDevMessage.objects.count(), 0)
        agent_run.assert_not_called()
        parser_run.assert_not_called()

    def test_scoped_tool_wrappers_hide_scope_and_store_safe_tool_call_summary(self):
        session = self.create_session()
        message = SeniorDevMessage.objects.create(session=session, role=SeniorDevMessage.Role.USER, text_content='Search auth')
        tools = senior_dev_scoped_tools_create(session=session, message=message)
        search_tool = next(tool for tool in tools if tool.__name__ == 'search_code')

        self.assertNotIn('project_id', inspect.signature(search_tool).parameters)
        self.assertNotIn('current_user_id', inspect.signature(search_tool).parameters)
        self.assertNotIn('commit_sha', inspect.signature(search_tool).parameters)

        with patch.object(senior_dev_scoped_tools_create_module, 'sr_dev_search_repository_code') as search_code:
            search_code.return_value = {
                'ok': True,
                'project_id': self.project.id,
                'repository': 'octocat/hello-world',
                'commit_sha': 'abc123',
                'query': 'rate limit',
                'results': [{'path': 'auth/views.py', 'line_number': 42, 'snippet': 'no throttle'}],
                'result_count': 1,
                'scanned_files': 1,
                'truncated': False,
            }
            result = search_tool(query='rate limit')

        tool_call = SeniorDevToolCall.objects.get(message=message)
        self.assertTrue(result['ok'])
        search_code.assert_called_once_with(
            project_id=self.project.id,
            current_user_id=self.member.id,
            commit_sha='abc123',
            query='rate limit',
            path_prefix='',
            file_extensions=[],
        )
        self.assertEqual(tool_call.tool_name, 'search_code')
        self.assertEqual(tool_call.commit_sha, 'abc123')
        self.assertEqual(tool_call.safe_result_summary['results'][0]['path'], 'auth/views.py')
        self.assertNotIn('content', tool_call.safe_result_summary)

    @patch.object(senior_dev_message_process_module, 'senior_dev_parser_run')
    @patch.object(senior_dev_message_process_module, 'senior_dev_agent_run')
    def test_parser_failure_returns_fallback_and_stores_raw_assistant_message(self, agent_run, parser_run):
        session = self.create_session()
        agent_run.return_value = 'Raw assistant reply'
        parser_run.side_effect = ValueError('bad parser output')

        response = self.client.post(
            reverse('api:agents:senior-dev-message-list', kwargs={'version': 'v1', 'session_id': session.id}),
            {'input_type': 'text', 'text': 'Check rate limiting.'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        assistant_message = SeniorDevMessage.objects.get(role=SeniorDevMessage.Role.ASSISTANT)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['assistant_message'], 'Raw assistant reply')
        self.assertEqual(assistant_message.text_content, 'Raw assistant reply')
        self.assertIn('bad parser output', assistant_message.structured_payload['parser_error'])

    @patch.object(senior_dev_message_process_module, 'senior_dev_parser_run')
    @patch.object(senior_dev_message_process_module, 'senior_dev_agent_run')
    def test_agent_failure_returns_safe_message_without_claims_or_findings(self, agent_run, parser_run):
        session = self.create_session()
        agent_run.side_effect = RuntimeError('model unavailable')

        response = self.client.post(
            reverse('api:agents:senior-dev-message-list', kwargs={'version': 'v1', 'session_id': session.id}),
            {'input_type': 'text', 'text': 'Check rate limiting.'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        assistant_message = SeniorDevMessage.objects.get(role=SeniorDevMessage.Role.ASSISTANT)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['agent_error']['code'], 'agent_error')
        self.assertEqual(assistant_message.structured_payload['agent_error']['code'], 'agent_error')
        self.assertEqual(SeniorDevClaim.objects.count(), 0)
        self.assertEqual(SeniorDevFinding.objects.count(), 0)
        parser_run.assert_not_called()

    @patch.object(senior_dev_message_process_module, 'senior_dev_parser_run')
    @patch.object(senior_dev_message_process_module, 'senior_dev_agent_run')
    def test_findings_without_tool_proof_are_rejected_not_persisted(self, agent_run, parser_run):
        session = self.create_session()
        agent_run.return_value = 'I think rate limiting is missing.'
        parser_run.return_value = {
            'assistant_message': 'I think rate limiting is missing.',
            'check_in_question': '',
            'choices': [],
            'allow_free_text': True,
            'claims': [{'text': 'Login is verified', 'status': 'verified'}],
            'findings': [{'title': 'Missing rate limiting', 'severity': 'high', 'evidence': [{'type': 'code', 'path': 'auth/views.py'}]}],
        }

        response = self.client.post(
            reverse('api:agents:senior-dev-message-list', kwargs={'version': 'v1', 'session_id': session.id}),
            {'input_type': 'text', 'text': 'We handle login safely.'},
            content_type='application/json',
            **self.auth_header(self.member),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['findings'], [])
        self.assertEqual(response.json()['rejected_findings'][0]['reason'], 'missing_get_context_tool_call')
        self.assertEqual(SeniorDevFinding.objects.count(), 0)
        self.assertEqual(SeniorDevClaim.objects.get().status, SeniorDevClaim.Status.UNVERIFIED)

    @patch.object(senior_dev_message_process_module, 'project_manager_agent_process_handoff')
    @patch.object(senior_dev_message_process_module, 'senior_dev_parser_run')
    @patch.object(senior_dev_message_process_module, 'senior_dev_agent_run')
    def test_pm_handoff_failure_keeps_sr_dev_message_successful_and_finding_open(self, agent_run, parser_run, pm_handoff):
        session = self.create_session()
        agent_run.side_effect = lambda *, session, user_message, tools: (
            self.create_tool_proof_for_message(session, user_message)
            or 'I checked the login endpoint and rate limiting appears missing.'
        )
        pm_handoff.return_value = {'ok': False, 'code': 'agent_error', 'detail': 'PM unavailable'}
        parser_run.return_value = {
            'assistant_message': 'I checked the login endpoint and rate limiting appears missing.',
            'check_in_question': '',
            'choices': [],
            'allow_free_text': True,
            'conversation_summary': 'Rate limit review.',
            'claims': [],
            'findings': [
                {
                    'type': 'vulnerability',
                    'title': 'Missing rate limiting on login endpoint',
                    'severity': 'high',
                    'confidence_score': 85,
                    'confidence_reason': 'Tool evidence found no throttling.',
                    'evidence': [{'type': 'code', 'path': 'auth/views.py', 'start_line': 42, 'snippet': 'Login view has no rate limit'}],
                }
            ],
        }

        response = self.client.post(
            reverse('api:agents:senior-dev-message-list', kwargs={'version': 'v1', 'session_id': session.id}),
            {'input_type': 'text', 'text': 'We already handle login safely.'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        assistant_message = SeniorDevMessage.objects.get(role=SeniorDevMessage.Role.ASSISTANT)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()['pm_handoff_result']['ok'])
        self.assertEqual(SeniorDevFinding.objects.get().status, SeniorDevFinding.Status.OPEN)
        self.assertFalse(assistant_message.structured_payload['pm_handoff_result']['ok'])

    def test_session_memory_context_is_limited_to_current_session(self):
        session = self.create_session()
        other_session = self.create_session()
        SeniorDevMessage.objects.create(session=session, role=SeniorDevMessage.Role.USER, text_content='Please review login throttling.')
        SeniorDevMessage.objects.create(session=session, role=SeniorDevMessage.Role.ASSISTANT, text_content='I found the auth view.')
        SeniorDevMessage.objects.create(session=other_session, role=SeniorDevMessage.Role.USER, text_content='Unrelated billing topic.')
        current_message = SeniorDevMessage.objects.create(session=session, role=SeniorDevMessage.Role.USER, text_content='What did we discuss?')

        context = senior_dev_memory_module.senior_dev_session_memory_context_build(session=session, before_message=current_message)

        self.assertIn('Please review login throttling.', context)
        self.assertIn('I found the auth view.', context)
        self.assertNotIn('Unrelated billing topic.', context)
        self.assertNotIn('What did we discuss?', context)

    def test_finding_status_patch_is_member_scoped_and_validates_status(self):
        session = self.create_session()
        message = SeniorDevMessage.objects.create(session=session, role=SeniorDevMessage.Role.ASSISTANT, text_content='Finding')
        finding = SeniorDevFinding.objects.create(session=session, message=message, title='Missing throttling')

        success_response = self.client.patch(
            reverse(
                'api:agents:senior-dev-finding-detail',
                kwargs={'version': 'v1', 'session_id': session.id, 'finding_id': finding.id},
            ),
            {'status': SeniorDevFinding.Status.DISMISSED},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        invalid_response = self.client.patch(
            reverse(
                'api:agents:senior-dev-finding-detail',
                kwargs={'version': 'v1', 'session_id': session.id, 'finding_id': finding.id},
            ),
            {'status': 'resolved'},
            content_type='application/json',
            **self.auth_header(self.member),
        )
        outsider_response = self.client.patch(
            reverse(
                'api:agents:senior-dev-finding-detail',
                kwargs={'version': 'v1', 'session_id': session.id, 'finding_id': finding.id},
            ),
            {'status': SeniorDevFinding.Status.OPEN},
            content_type='application/json',
            **self.auth_header(self.outsider),
        )

        self.assertEqual(success_response.status_code, status.HTTP_200_OK)
        self.assertEqual(success_response.json()['status'], SeniorDevFinding.Status.DISMISSED)
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(outsider_response.status_code, status.HTTP_404_NOT_FOUND)
