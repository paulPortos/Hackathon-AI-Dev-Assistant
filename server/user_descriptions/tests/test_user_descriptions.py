from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from user_descriptions.models import UserDescription
from user_descriptions.selectors import user_description_get_agent_context
from users.models import User


class UserDescriptionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            github_id='123',
            username='backend-dev',
            name='Backend Dev',
            email='backend@example.com',
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_me_returns_404_when_description_missing(self):
        response = self.client.get(
            reverse('api-v1:user-descriptions:user-description-me', kwargs={'version': 'v1'}),
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_me_creates_description(self):
        response = self.client.patch(
            reverse('api-v1:user-descriptions:user-description-me', kwargs={'version': 'v1'}),
            {
                'primary_role': 'backend',
                'experience_level': 'mid',
                'summary': 'Builds Django APIs and database features.',
                'skills': [{'name': 'Django', 'level': 4}],
                'preferred_tasks': ['backend_api', 'database', 'backend_api'],
                'avoided_tasks': ['frontend_ui'],
                'availability_notes': 'Weeknights only',
                'agent_notes': 'Best fit for backend work.',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['primary_role'], 'backend')
        self.assertEqual(payload['skills'], [{'name': 'Django', 'level': 4}])
        self.assertEqual(payload['preferred_tasks'], ['backend_api', 'database'])
        self.assertEqual(UserDescription.objects.count(), 1)

    def test_patch_me_updates_existing_description(self):
        UserDescription.objects.create(user=self.user, primary_role='frontend', summary='Old')

        response = self.client.patch(
            reverse('api-v1:user-descriptions:user-description-me', kwargs={'version': 'v1'}),
            {'primary_role': 'fullstack', 'summary': 'Now handles frontend and backend.'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserDescription.objects.count(), 1)
        user_description = UserDescription.objects.get(user=self.user)
        self.assertEqual(user_description.primary_role, 'fullstack')
        self.assertEqual(user_description.summary, 'Now handles frontend and backend.')

    def test_patch_me_validates_skills(self):
        response = self.client.patch(
            reverse('api-v1:user-descriptions:user-description-me', kwargs={'version': 'v1'}),
            {'skills': [{'name': 'Django', 'level': 6}]},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('skills', response.json())

    def test_list_endpoint_is_paginated(self):
        UserDescription.objects.create(user=self.user, primary_role='backend')

        response = self.client.get(
            reverse('api-v1:user-descriptions:user-description-list', kwargs={'version': 'v1'}),
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['count'], 1)
        self.assertIn('results', payload)
        self.assertEqual(payload['results'][0]['primary_role'], 'backend')

    def test_detail_endpoint_returns_single_description(self):
        user_description = UserDescription.objects.create(user=self.user, primary_role='backend')

        response = self.client.get(
            reverse(
                'api-v1:user-descriptions:user-description-detail',
                kwargs={'version': 'v1', 'pk': user_description.id},
            ),
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['id'], user_description.id)

    def test_agent_context_selector_returns_compact_context(self):
        user_description = UserDescription.objects.create(
            user=self.user,
            primary_role='backend',
            experience_level='mid',
            skills=[{'name': 'Django', 'level': 4}],
            preferred_tasks=['backend_api'],
            avoided_tasks=['frontend_ui'],
            agent_notes='Give backend tickets.',
        )

        context = user_description_get_agent_context(user_description)

        self.assertEqual(context['user']['username'], 'backend-dev')
        self.assertEqual(context['primary_role'], 'backend')
        self.assertEqual(context['skills'], [{'name': 'Django', 'level': 4}])
        self.assertEqual(context['preferred_tasks'], ['backend_api'])
