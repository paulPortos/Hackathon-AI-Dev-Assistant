from django.contrib.auth.hashers import identify_hasher
from django.test import TestCase

from users.models import User


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
