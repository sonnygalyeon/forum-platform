from django.test import TestCase

from apps.identity.services import level_for_reputation


class IdentityLevelTests(TestCase):
    def test_level_thresholds(self):
        self.assertEqual(level_for_reputation(0), 1)
        self.assertEqual(level_for_reputation(24), 1)
        self.assertEqual(level_for_reputation(25), 2)
        self.assertGreaterEqual(level_for_reputation(600), 6)
