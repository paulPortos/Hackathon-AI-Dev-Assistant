from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status

from users.models import User
from users.views import GITHUB_OAUTH_STATE_SESSION_KEY


@override_settings(
    GITHUB_CLIENT_ID='client-id',
    GITHUB_CLIENT_SECRET='client-secret',
    GITHUB_CALLBACK_URL='http://localhost:8000/auth/github/callback/',
)
class GitHubOAuthTests(TestCase):
    def test_login_redirects_to_github_and_stores_state(self):
        response = self.client.get(reverse('auth:github-login'))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        parsed = urlparse(response['Location'])
        query = parse_qs(parsed.query)
        session = self.client.session

        self.assertEqual(f'{parsed.scheme}://{parsed.netloc}{parsed.path}', 'https://github.com/login/oauth/authorize')
        self.assertEqual(query['client_id'], ['client-id'])
        self.assertEqual(query['redirect_uri'], ['http://localhost:8000/auth/github/callback/'])
        self.assertEqual(query['scope'], ['read:user user:email'])
        self.assertEqual(query['state'], [session[GITHUB_OAUTH_STATE_SESSION_KEY]])

    def test_callback_requires_valid_state(self):
        response = self.client.get(reverse('auth:github-callback'), {'code': 'code', 'state': 'bad'})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'Invalid GitHub OAuth state')

    def test_callback_handles_github_error_response(self):
        session = self.client.session
        session[GITHUB_OAUTH_STATE_SESSION_KEY] = 'state'
        session.save()

        response = self.client.get(
            reverse('auth:github-callback'),
            {'error': 'access_denied', 'error_description': 'Denied', 'state': 'state'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Denied')

    @patch('users.views.fetch_github_emails')
    @patch('users.views.fetch_github_user')
    @patch('users.views.exchange_code_for_access_token')
    def test_callback_creates_user_and_returns_tokens(self, exchange_code, fetch_user, fetch_emails):
        exchange_code.return_value = 'github-token'
        fetch_user.return_value = {
            'id': 123,
            'login': 'octocat',
            'name': 'Octo Cat',
            'email': None,
            'avatar_url': 'https://avatars.githubusercontent.com/u/123',
        }
        fetch_emails.return_value = [
            {'email': 'secondary@example.com', 'primary': False, 'verified': True},
            {'email': 'octocat@example.com', 'primary': True, 'verified': True},
        ]
        session = self.client.session
        session[GITHUB_OAUTH_STATE_SESSION_KEY] = 'state'
        session.save()

        response = self.client.get(reverse('auth:github-callback'), {'code': 'code', 'state': 'state'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn('access', payload)
        self.assertIn('refresh', payload)
        self.assertNotIn('access_token', payload['user'])
        self.assertEqual(payload['user']['email'], 'octocat@example.com')

        user = User.objects.get(github_id='123')
        self.assertEqual(user.username, 'octocat')
        self.assertEqual(user.name, 'Octo Cat')
        self.assertEqual(user.email, 'octocat@example.com')
        self.assertEqual(user.access_token, 'github-token')

    @patch('users.views.fetch_github_emails')
    @patch('users.views.fetch_github_user')
    @patch('users.views.exchange_code_for_access_token')
    def test_callback_updates_existing_user(self, exchange_code, fetch_user, fetch_emails):
        User.objects.create_user(github_id='123', username='old', email='old@example.com')
        exchange_code.return_value = 'new-token'
        fetch_user.return_value = {
            'id': 123,
            'login': 'new-login',
            'name': 'New Name',
            'email': 'profile@example.com',
            'avatar_url': 'https://avatars.githubusercontent.com/u/123',
        }
        fetch_emails.return_value = []
        session = self.client.session
        session[GITHUB_OAUTH_STATE_SESSION_KEY] = 'state'
        session.save()

        response = self.client.get(reverse('auth:github-callback'), {'code': 'code', 'state': 'state'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(github_id='123')
        self.assertEqual(user.username, 'new-login')
        self.assertEqual(user.email, 'profile@example.com')
        self.assertEqual(user.access_token, 'new-token')
