from datetime import timedelta
import importlib
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import EmailVerificationCode
from users.models import User


request_service_module = importlib.import_module('users.services.email_verification_request_for_user')


@override_settings(
    TWILLIO_SENDGRID_API_KEY='sendgrid-key',
    TWILLIO_SENDGRID_FROM_EMAIL='noreply@example.com',
    EMAIL_VERIFICATION_CODE_TTL_MINUTES=10,
    EMAIL_VERIFICATION_MAX_ATTEMPTS=5,
    EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=60,
)
class EmailVerificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            github_id='123',
            username='octocat',
            email='octocat@example.com',
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    @patch.object(request_service_module, 'send_email_verification_code')
    def test_request_endpoint_sends_code(self, send_email):
        response = self.client.post(
            reverse('users-api:email-verification-request', kwargs={'version': 'v1'}),
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['detail'], 'Verification code sent')
        send_email.assert_called_once()

        verification_code = EmailVerificationCode.objects.get(user=self.user)
        sent_code = send_email.call_args.kwargs['code']
        self.assertRegex(sent_code, r'^\d{6}$')
        self.assertTrue(check_password(sent_code, verification_code.code_hash))

    @patch.object(request_service_module, 'send_email_verification_code')
    def test_request_endpoint_rejects_user_without_email(self, send_email):
        self.user.email = ''
        self.user.save(update_fields=['email'])

        response = self.client.post(
            reverse('users-api:email-verification-request', kwargs={'version': 'v1'}),
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'User does not have an email address')
        send_email.assert_not_called()

    @patch.object(request_service_module, 'send_email_verification_code')
    def test_request_endpoint_enforces_cooldown(self, send_email):
        EmailVerificationCode.objects.create(
            user=self.user,
            sent_to_email=self.user.email,
            code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now(),
        )

        response = self.client.post(
            reverse('users-api:email-verification-request', kwargs={'version': 'v1'}),
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Please wait before requesting another verification code')
        send_email.assert_not_called()

    def test_confirm_endpoint_accepts_correct_code(self):
        verification_code = EmailVerificationCode.objects.create(
            user=self.user,
            sent_to_email=self.user.email,
            code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now() - timedelta(minutes=2),
        )

        response = self.client.post(
            reverse('users-api:email-verification-confirm', kwargs={'version': 'v1'}),
            {'code': '123456'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['detail'], 'Email verified')
        self.user.refresh_from_db()
        verification_code.refresh_from_db()
        self.assertIsNotNone(self.user.email_verified_at)
        self.assertIsNotNone(verification_code.consumed_at)
        self.assertIn('email_verified_at', response.json()['user'])

    def test_confirm_endpoint_rejects_invalid_format(self):
        response = self.client.post(
            reverse('users-api:email-verification-confirm', kwargs={'version': 'v1'}),
            {'code': 'abc'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.json())

    def test_confirm_endpoint_rejects_wrong_code(self):
        EmailVerificationCode.objects.create(
            user=self.user,
            sent_to_email=self.user.email,
            code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now() - timedelta(minutes=2),
        )

        response = self.client.post(
            reverse('users-api:email-verification-confirm', kwargs={'version': 'v1'}),
            {'code': '654321'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Verification code is invalid')
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertEqual(verification_code.attempt_count, 1)

    def test_confirm_endpoint_rejects_expired_code(self):
        EmailVerificationCode.objects.create(
            user=self.user,
            sent_to_email=self.user.email,
            code_hash=make_password('123456'),
            expires_at=timezone.now() - timedelta(minutes=1),
            last_sent_at=timezone.now() - timedelta(minutes=20),
        )

        response = self.client.post(
            reverse('users-api:email-verification-confirm', kwargs={'version': 'v1'}),
            {'code': '123456'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Verification code has expired')

    def test_confirm_endpoint_rejects_consumed_code(self):
        EmailVerificationCode.objects.create(
            user=self.user,
            sent_to_email=self.user.email,
            code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10),
            consumed_at=timezone.now(),
            last_sent_at=timezone.now() - timedelta(minutes=2),
        )

        response = self.client.post(
            reverse('users-api:email-verification-confirm', kwargs={'version': 'v1'}),
            {'code': '123456'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Verification code has already been used')

    def test_confirm_endpoint_rejects_too_many_attempts(self):
        EmailVerificationCode.objects.create(
            user=self.user,
            sent_to_email=self.user.email,
            code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10),
            attempt_count=5,
            last_sent_at=timezone.now() - timedelta(minutes=2),
        )

        response = self.client.post(
            reverse('users-api:email-verification-confirm', kwargs={'version': 'v1'}),
            {'code': '123456'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Too many verification attempts')

    def test_user_serializer_includes_email_verified_at(self):
        from users.serializers import UserSerializer

        payload = UserSerializer(self.user).data

        self.assertIn('email_verified_at', payload)
