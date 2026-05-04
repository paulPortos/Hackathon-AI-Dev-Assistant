import json
import logging

from django.test import TestCase, override_settings
from django.urls import path
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.logging.structured_json_formatter import StructuredJsonFormatter


class EchoView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({'ok': True})


class UnexpectedErrorView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        raise RuntimeError('database password leaked in internal traceback')


class ValidationErrorView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        raise ValidationError({'name': ['This field is required.']})


urlpatterns = [
    path('echo/', EchoView.as_view(), name='echo'),
    path('unexpected-error/', UnexpectedErrorView.as_view(), name='unexpected-error'),
    path('validation-error/', ValidationErrorView.as_view(), name='validation-error'),
]


@override_settings(ROOT_URLCONF=__name__)
class SecurityAuditTests(TestCase):
    def test_response_includes_request_id_header(self):
        response = self.client.get('/echo/', HTTP_X_REQUEST_ID='request-123')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['X-Request-ID'], 'request-123')

    def test_request_audit_log_is_structured_json_metadata(self):
        with self.assertLogs('security.audit', level='INFO') as captured_logs:
            response = self.client.get(
                '/echo/',
                HTTP_AUTHORIZATION='Bearer secret-access-token',
                HTTP_USER_AGENT='SecurityAuditTests',
                HTTP_X_REQUEST_ID='audit-123',
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record = captured_logs.records[0]
        formatted_log = StructuredJsonFormatter().format(record)
        payload = json.loads(formatted_log)

        self.assertEqual(payload['message'], 'request_completed')
        self.assertEqual(payload['request_id'], 'audit-123')
        self.assertEqual(payload['method'], 'GET')
        self.assertEqual(payload['path'], '/echo/')
        self.assertEqual(payload['status_code'], status.HTTP_200_OK)
        self.assertIn('duration_ms', payload)
        self.assertNotIn('secret-access-token', formatted_log)
        self.assertNotIn('Authorization', formatted_log)

    def test_unexpected_api_error_returns_friendly_response_and_logs_real_exception(self):
        with self.assertLogs('api.errors', level='ERROR') as captured_logs:
            response = self.client.get('/unexpected-error/', HTTP_X_REQUEST_ID='error-123')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        payload = response.json()
        self.assertEqual(payload['detail'], 'Something went wrong. Please try again.')
        self.assertEqual(payload['code'], 'server_error')
        self.assertEqual(payload['request_id'], 'error-123')
        self.assertEqual(response['X-Request-ID'], 'error-123')
        self.assertNotIn('database password leaked', json.dumps(payload))

        record = captured_logs.records[0]
        formatted_log = StructuredJsonFormatter().format(record)
        log_payload = json.loads(formatted_log)
        self.assertEqual(log_payload['message'], 'unhandled_api_exception')
        self.assertEqual(log_payload['request_id'], 'error-123')
        self.assertEqual(log_payload['exception_class'], 'RuntimeError')
        self.assertIn('database password leaked in internal traceback', log_payload['exception'])

    def test_validation_error_remains_client_friendly_and_specific(self):
        response = self.client.get('/validation-error/', HTTP_X_REQUEST_ID='validation-123')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'name': ['This field is required.']})
        self.assertEqual(response['X-Request-ID'], 'validation-123')

    def test_suspicious_sql_like_input_is_logged_without_blocking_or_raw_values(self):
        with self.assertLogs('security.suspicious_input', level='WARNING') as captured_logs:
            response = self.client.get(
                '/echo/',
                {
                    'q': "' OR 1=1 --",
                    'access_token': 'DROP TABLE users',
                },
                HTTP_X_REQUEST_ID='suspicious-123',
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record = captured_logs.records[0]
        formatted_log = StructuredJsonFormatter().format(record)
        payload = json.loads(formatted_log)
        fields = [signal['field'] for signal in payload['signals']]

        self.assertEqual(payload['message'], 'suspicious_input_detected')
        self.assertEqual(payload['request_id'], 'suspicious-123')
        self.assertIn('q', fields)
        self.assertIn('[redacted]', fields)
        self.assertNotIn("' OR 1=1", formatted_log)
        self.assertNotIn('DROP TABLE users', formatted_log)
        self.assertNotIn('access_token', formatted_log)

    def test_structured_json_formatter_outputs_valid_json(self):
        record = logging.getLogger('security.audit').makeRecord(
            'security.audit',
            logging.INFO,
            __file__,
            1,
            'request_completed',
            args=(),
            exc_info=None,
            extra={'request_id': 'formatter-123', 'status_code': status.HTTP_200_OK},
        )

        payload = json.loads(StructuredJsonFormatter().format(record))

        self.assertEqual(payload['logger'], 'security.audit')
        self.assertEqual(payload['message'], 'request_completed')
        self.assertEqual(payload['request_id'], 'formatter-123')
        self.assertEqual(payload['status_code'], status.HTTP_200_OK)
