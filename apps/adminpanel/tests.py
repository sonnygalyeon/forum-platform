from django.test import TestCase


class AdminPanelSmokeTests(TestCase):
    def test_module_loads(self):
        from apps.adminpanel.api import urls  # noqa: F401
