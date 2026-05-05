from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User


class UserSearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            github_id='123',
            username='octocat',
            email='octocat@example.com',
            access_token='secret-token',
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_user_search_matches_username(self):
        match = User.objects.create_user(
            github_id='456',
            username='frontend-dev',
            name='Frontend Dev',
            email='frontend@example.com',
            access_token='other-secret-token',
        )
        User.objects.create_user(
            github_id='789',
            username='backend-dev',
            email='backend@example.com',
        )

        response = self.client.get(
            reverse('api:users:user-search', kwargs={'version': 'v1'}),
            {'q': 'front'},
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['count'], 1)
        result = payload['results'][0]
        self.assertEqual(result['id'], match.id)
        self.assertEqual(result['username'], 'frontend-dev')
        self.assertNotIn('email', result)
        self.assertNotIn('access_token', result)
        self.assertNotIn('github_id', result)

    def test_user_search_matches_email(self):
        match = User.objects.create_user(
            github_id='456',
            username='frontend-dev',
            email='frontend@example.com',
        )

        response = self.client.get(
            reverse('api:users:user-search', kwargs={'version': 'v1'}),
            {'q': 'FRONTEND@EXAMPLE'},
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['count'], 1)
        self.assertEqual(payload['results'][0]['id'], match.id)

    def test_user_search_returns_empty_results_for_blank_query(self):
        User.objects.create_user(
            github_id='456',
            username='frontend-dev',
            email='frontend@example.com',
        )

        response = self.client.get(
            reverse('api:users:user-search', kwargs={'version': 'v1'}),
            {'q': '   '},
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['count'], 0)
        self.assertEqual(payload['results'], [])

    def test_user_search_requires_authentication(self):
        response = self.client.get(
            reverse('api:users:user-search', kwargs={'version': 'v1'}),
            {'q': 'front'},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
