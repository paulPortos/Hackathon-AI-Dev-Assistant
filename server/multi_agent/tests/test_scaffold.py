from django.apps import apps
from django.test import SimpleTestCase

from multi_agent import agents


class MultiAgentScaffoldTests(SimpleTestCase):
    def test_multi_agent_app_is_installed(self):
        self.assertTrue(apps.is_installed('multi_agent'))

    def test_agent_packages_are_importable(self):
        self.assertTrue(hasattr(agents, '__path__'))
