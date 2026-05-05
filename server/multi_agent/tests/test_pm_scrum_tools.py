from datetime import datetime, time
from importlib import import_module
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import TestCase

from multi_agent.agents.pm.tools import (
    pm_assign_task_to_best_member,
    pm_get_project_context,
)
from multi_agent.agents.scrum.tools import (
    scrum_generate_meeting_summary,
    scrum_get_meeting_settings,
    scrum_send_due_reminder_emails,
)
from projects.models import Project, ProjectAuditLog, ProjectMeetingSettings, ProjectMember, ProjectTask, ProjectVulnerability
from projects.services import project_task_create, project_vulnerability_create
from user_descriptions.models import UserDescription
from users.models import User


scrum_send_due_reminder_emails_module = import_module('multi_agent.agents.scrum.tools.scrum_send_due_reminder_emails')


class PmAndScrumToolTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            github_id='101',
            username='creator',
            name='Creator',
            email='creator@example.com',
        )
        self.backend = User.objects.create_user(
            github_id='102',
            username='backend',
            name='Backend Dev',
            email='backend@example.com',
        )
        self.frontend = User.objects.create_user(
            github_id='103',
            username='frontend',
            name='Frontend Dev',
            email='frontend@example.com',
        )
        self.outsider = User.objects.create_user(
            github_id='104',
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
            overview='AI dev assistant',
            goals='Ship safer vibe-coded projects',
            tech_stack=['Django', 'DRF'],
            business_context='Hackathon MVP',
            agent_notes='Favor security fixes first',
        )
        self.creator_member = ProjectMember.objects.create(
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
        self.frontend_member = ProjectMember.objects.create(
            project=self.project,
            user=self.frontend,
            invited_by=self.creator,
            display_role='Frontend Developer',
            roles=['frontend'],
        )
        UserDescription.objects.create(
            user=self.backend,
            primary_role='backend',
            experience_level='senior',
            summary='Builds secure Django APIs and auth flows.',
            skills=[{'name': 'Django', 'level': 5}, {'name': 'security', 'level': 4}],
            preferred_tasks=['vulnerability_fix', 'backend_api'],
            avoided_tasks=['frontend_ui'],
            availability_notes='Available weekdays',
        )
        UserDescription.objects.create(
            user=self.frontend,
            primary_role='frontend',
            experience_level='mid',
            summary='Builds React screens.',
            skills=[{'name': 'React', 'level': 4}],
            preferred_tasks=['frontend_ui'],
            avoided_tasks=['vulnerability_fix'],
        )

    def test_pm_get_project_context_returns_project_members_tasks_and_vulnerabilities(self):
        project_task_create(project=self.project, data={'title': 'Open task', 'assigned_to': self.backend_member})
        project_vulnerability_create(project=self.project, data={'title': 'Open vuln', 'severity': 'high'})

        payload = pm_get_project_context(project_id=self.project.id, current_user_id=self.backend.id)

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['project_context']['project']['github_full_name'], 'octocat/hello-world')
        self.assertEqual(payload['open_tasks'][0]['title'], 'Open task')
        self.assertEqual(payload['unresolved_vulnerabilities'][0]['title'], 'Open vuln')

    def test_pm_assign_task_to_best_member_uses_role_skills_preferences_and_load(self):
        payload = pm_assign_task_to_best_member(
            project_id=self.project.id,
            current_user_id=self.creator.id,
            task_context={
                'title': 'Fix auth token leak',
                'description': 'Move secret handling into environment variables.',
                'category': 'vulnerability_fix',
                'required_skills': ['Django', 'security'],
            },
        )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['member']['id'], self.backend_member.id)
        self.assertIn('Role fits', payload['reasoning'])

    def test_scrum_tools_read_settings_and_generate_structured_summary(self):
        ProjectMeetingSettings.objects.create(
            project=self.project,
            meeting_days=['monday'],
            meeting_time=time(10, 0),
            timezone='Asia/Manila',
            google_meet_link='https://meet.google.com/abc-defg-hij',
            weekly_goals='Close security blockers.',
            monthly_goals='Launch the MVP.',
            alert_minutes_before=30,
        )
        project_task_create(
            project=self.project,
            data={'title': 'Fix auth leak', 'assigned_to': self.backend_member, 'priority': ProjectTask.Priority.CRITICAL},
        )
        project_task_create(
            project=self.project,
            data={'title': 'Blocked infra task', 'assigned_to': self.backend_member, 'status': ProjectTask.Status.BLOCKED},
        )
        project_task_create(project=self.project, data={'title': 'Completed docs', 'status': ProjectTask.Status.COMPLETED})
        project_vulnerability_create(project=self.project, data={'title': 'High auth risk', 'severity': 'high'})

        settings_payload = scrum_get_meeting_settings(self.project.id, self.backend.id)
        summary_payload = scrum_generate_meeting_summary(self.project.id, self.backend.id)

        self.assertTrue(settings_payload['ok'])
        self.assertEqual(settings_payload['meeting_settings']['google_meet_link'], 'https://meet.google.com/abc-defg-hij')
        self.assertTrue(summary_payload['ok'])
        self.assertEqual(summary_payload['summary']['meeting']['google_meet_link'], 'https://meet.google.com/abc-defg-hij')
        self.assertEqual(summary_payload['summary']['open_tasks'][0]['title'], 'Fix auth leak')
        self.assertEqual(summary_payload['summary']['blockers'][0]['title'], 'Blocked infra task')
        self.assertNotIn('Blocked infra task', [task['title'] for task in summary_payload['summary']['open_tasks']])
        self.assertEqual(summary_payload['summary']['unresolved_vulnerabilities'][0]['title'], 'High auth risk')

    def test_scrum_send_due_reminder_emails_returns_per_project_results(self):
        ProjectMeetingSettings.objects.create(
            project=self.project,
            meeting_days=['monday'],
            meeting_time=time(10, 0),
            timezone='Asia/Manila',
            google_meet_link='https://meet.google.com/abc-defg-hij',
            alert_minutes_before=30,
        )

        with patch.object(scrum_send_due_reminder_emails_module, 'project_meeting_reminder_send') as send_reminder:
            payload = scrum_send_due_reminder_emails('2026-05-04T01:30:00+00:00')

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['sent_count'], 1)
        self.assertEqual(payload['failed_count'], 0)
        send_reminder.assert_called_once()
