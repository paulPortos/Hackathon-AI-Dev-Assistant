from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User


class PublicUserDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            github_id='123',
            username='octocat',
            email='octocat@example.com',
            access_token='secret-token',
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_public_user_detail_returns_safe_fields(self):
        other_user = User.objects.create_user(
            github_id='456',
            username='frontend-dev',
            name='Frontend Dev',
            email='frontend@example.com',
            avatar_url='https://example.com/avatar.png',
            access_token='other-secret-token',
        )

        response = self.client.get(
            reverse('api:users:user-detail', kwargs={'version': 'v1', 'user_id': other_user.id}),
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['id'], other_user.id)
        self.assertEqual(payload['username'], 'frontend-dev')
        self.assertEqual(payload['name'], 'Frontend Dev')
        self.assertEqual(payload['avatar_url'], 'https://example.com/avatar.png')
        self.assertNotIn('email', payload)
        self.assertNotIn('access_token', payload)
        self.assertNotIn('github_id', payload)

    def test_public_user_detail_404s_when_missing(self):
        response = self.client.get(
            reverse('api:users:user-detail', kwargs={'version': 'v1', 'user_id': 9999}),
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
