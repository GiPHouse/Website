from django.test import TestCase

from projects import awssync


class AWSSyncTest(TestCase):
    """Test AWSSync class."""

    def setUp(self):
        self.sync = awssync.AWSSync()

    def test_button_pressed(self):
        return_value = self.sync.button_pressed()
        self.assertTrue(return_value)
