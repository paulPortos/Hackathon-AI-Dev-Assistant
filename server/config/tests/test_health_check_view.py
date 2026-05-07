from django.test import Client, SimpleTestCase
from django.urls import reverse


class HealthCheckViewTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_is_lightweight_and_unauthenticated(self):
        response = self.client.get(reverse('api:health-check', kwargs={'version': 'v1'}))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertEqual(response['X-Health-Check'], 'ok')

    def test_health_check_accepts_head(self):
        response = self.client.head(reverse('api:health-check', kwargs={'version': 'v1'}))

        self.assertEqual(response.status_code, 204)
