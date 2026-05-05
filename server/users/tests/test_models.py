import importlib
from unittest.mock import patch

from django.contrib.auth.hashers import identify_hasher
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from users.models import User
from users.services import github_access_token_get_valid


github_access_token_get_valid_module = importlib.import_module('users.services.github_access_token_get_valid')


class UserModelTests(TestCase):
    def test_create_superuser_hashes_password_with_argon2(self):
        user = User.objects.create_superuser(
            github_id='1',
            username='admin',
            email='admin@example.com',
            password='strong-password',
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password('strong-password'))
        self.assertEqual(identify_hasher(user.password).algorithm, 'argon2')

    def test_github_tokens_are_encrypted_at_rest(self):
        user = User.objects.create_user(
            github_id='2',
            username='octocat',
            access_token='plain-access-token',
            github_refresh_token='plain-refresh-token',
        )

        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT access_token, github_refresh_token FROM users_user WHERE id = %s',
                [user.id],
            )
            access_token, refresh_token = cursor.fetchone()

        self.assertNotEqual(access_token, 'plain-access-token')
        self.assertNotEqual(refresh_token, 'plain-refresh-token')
        self.assertTrue(access_token.startswith('gAAAAA'))
        self.assertTrue(refresh_token.startswith('gAAAAA'))

        user.refresh_from_db()
        self.assertEqual(user.access_token, 'plain-access-token')
        self.assertEqual(user.github_refresh_token, 'plain-refresh-token')

    def test_expired_github_token_refreshes_before_use(self):
        user = User.objects.create_user(
            github_id='3',
            username='refreshable',
            access_token='old-access-token',
            github_refresh_token='old-refresh-token',
            github_access_token_expires_at=timezone.now() - timezone.timedelta(minutes=5),
        )

        with patch.object(github_access_token_get_valid_module, 'refresh_github_access_token') as refresh_token:
            refresh_token.return_value = {
                'access_token': 'new-access-token',
                'refresh_token': 'new-refresh-token',
                'expires_in': 28800,
                'refresh_token_expires_in': 15897600,
            }

            access_token = github_access_token_get_valid(user)

        self.assertEqual(access_token, 'new-access-token')
        user.refresh_from_db()
        self.assertEqual(user.access_token, 'new-access-token')
        self.assertEqual(user.github_refresh_token, 'new-refresh-token')
        self.assertGreater(user.github_access_token_expires_at, timezone.now())
        refresh_token.assert_called_once_with(refresh_token='old-refresh-token')
