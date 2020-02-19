from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import MagicMock

from django.test import TestCase

# While testing, we do not want to speak with GitHub so we mock the packages that do so
with mock.patch("github.GithubIntegration") as mock_gi:
    with mock.patch("github.Github") as mock_github:
        from projects.githubsync import GitHubAPITalker
        from projects import githubsync


class GitHubAPITalkerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Setup test data to use in these tests."""
        cls.organization = "AGitHubOrganizationName"
        cls.app_id = 12345
        cls.installation_id = 1234567

    def setUp(self):
        """Create a mock pygithub object to talk with."""
        githubsync.talker.gi.get_access_token = MagicMock()
        self.talker = githubsync.talker

    def tearDown(self):
        """Remove  objects after a test is performed."""
        del self.talker

    def test___init__(self):
        """Test that when getting an API talker, the organization is set."""
        self.assertIsInstance(self.talker, GitHubAPITalker)
        self.assertIsNotNone(self.talker.organization)

    def test_renew_access_token_if_required__unexpired(self):
        """Test if when requesting an unexpired token, nothing happens."""
        self.talker.access_token = MagicMock()
        self.talker.gi.get_access_token = MagicMock()
        self.talker.access_token.expires_at = datetime.now() + timedelta(hours=1)
        self.talker.renew_access_token_if_required()
        self.talker.gi.get_access_token.assert_not_called()

    def test_renew_access_token_if_required__expired(self):
        """Test if when requesting an expired token, a new token is requested."""
        self.talker.access_token = MagicMock()
        self.talker.gi.get_access_token = MagicMock()
        self.talker.access_token.expires_at = datetime.now() - timedelta(hours=1)
        self.talker.renew_access_token_if_required()
        self.talker.gi.get_access_token.assert_called_once_with(self.talker.installation_id)

    def test_renew_access_token_if_required__no_token(self):
        """Test if when requesting a token when no token exists yet, a new token is requested."""
        self.talker.access_token = None
        self.talker.gi.get_access_token = MagicMock()
        self.talker.renew_access_token_if_required()
        self.talker.gi.get_access_token.assert_called_once_with(self.talker.installation_id)
