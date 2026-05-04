from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User


class MeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            github_id='123',
            username='octocat',
            email='octocat@example.com',
            access_token='secret-token',
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_api_v1_me_returns_current_user(self):
        response = self.client.get(
            reverse('api:users:current-user-detail', kwargs={'version': 'v1'}),
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['github_id'], '123')
        self.assertEqual(payload['username'], 'octocat')
        self.assertNotIn('access_token', payload)

    def test_unversioned_api_me_alias_is_not_available(self):
        response = self.client.get(
            '/api/me/',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
