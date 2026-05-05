from datetime import datetime, time, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo
from importlib import import_module

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from projects.models import Project, ProjectMember, ProjectTask
from scrum.models import ProjectMeetingSettings
from scrum.selectors import project_meeting_settings_due_for_reminder, project_meeting_settings_get_for_project
from scrum.services import project_meeting_reminder_send, project_meeting_settings_upsert
from projects.services import project_task_create, project_vulnerability_create
from users.models import User

project_meeting_reminder_send_service_module = import_module('scrum.services.meeting_reminder_send')


class MeetingSettingsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            github_id='1',
            username='creator',
            name='Creator',
            email='creator@example.com',
        )
        self.member = User.objects.create_user(
            github_id='2',
            username='member',
            name='Member',
            email='member@example.com',
        )

    def auth_header(self, user):
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    def create_project(self):
        project = Project.objects.create(
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
        ProjectMember.objects.create(
            project=project,
            user=self.creator,
            invited_by=self.creator,
            display_role='Owner',
            roles=['owner'],
        )
        return project

    def test_meeting_settings_management_view_validates_permission_and_structure(self):
        project = self.create_project()
        ProjectMember.objects.create(
            project=project,
            user=self.member,
            invited_by=self.creator,
            display_role='Developer',
            roles=['developer'],
        )

        # 1. Detail GET (NotFound initially)
        not_found_response = self.client.get(
            reverse('api:scrum:project-meeting-settings-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            **self.auth_header(self.creator),
        )
        self.assertEqual(not_found_response.status_code, status.HTTP_404_NOT_FOUND)

        # 2. Upsert via PUT
        payload = {
            'meeting_days': ['monday', 'wednesday'],
            'meeting_time': '10:00:00',
            'timezone': 'Asia/Manila',
            'google_meet_link': 'https://meet.google.com/abc-defg-hij',
        }
        create_response = self.client.put(
            reverse('api:scrum:project-meeting-settings-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            payload,
            content_type='application/json',
            **self.auth_header(self.creator),
        )

        # 3. Read by non-creator member
        member_read_response = self.client.get(
            reverse('api:scrum:project-meeting-settings-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            **self.auth_header(self.member),
        )

        # 4. Forbidden update by non-creator member
        forbidden_response = self.client.patch(
            reverse('api:scrum:project-meeting-settings-detail', kwargs={'version': 'v1', 'project_id': project.id}),
            {'meeting_days': ['friday']},
            content_type='application/json',
            **self.auth_header(self.member),
        )

        # 5. Successful partial update by creator
        creator_update_response = self.client.patch(
            reverse('api:scrum:project-meeting-settings-detail', kwargs={'version': 'v1', 'project_id': project.id}),
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
        self.assertEqual(kwargs['to_emails'], ['creator@example.com', 'member@example.com'])
        self.assertIn('https://meet.google.com/abc-defg-hij', kwargs['text_content'])
        self.assertIn('Ship the auth hardening sprint.', kwargs['text_content'])
        self.assertIn('Fix CORS configuration', kwargs['text_content'])
        self.assertIn('Leaked token risk', kwargs['text_content'])
        self.assertIn('Document threat model', kwargs['text_content'])
        meeting_settings.refresh_from_db()
        self.assertIsNotNone(meeting_settings.last_reminder_sent_at)
