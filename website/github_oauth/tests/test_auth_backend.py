from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.test import TestCase

from github_oauth.backends import GithubOAuthBackend

from registrations.models import GiphouseProfile

from requests.exceptions import RequestException

User: DjangoUser = get_user_model()


class GithubOAuthBackendTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Set up test user and GitHub data.
        """

        cls.github_id = 0
        cls.github_username = 'test_user'
        cls.github_code = 'fake code'
        cls.github_access_token = 'fake token'

        cls.test_user = User.objects.create_user(
            username=cls.github_username,
        )

        cls.test_giphouse_user = GiphouseProfile.objects.create(
            user=cls.test_user,
            github_id=cls.github_id,
        )

    def test_authenticate_success(self):
        """
        Test the authenticate() method if it succeeds.
        """
        backend = GithubOAuthBackend()

        backend.get_github_info = mock.MagicMock(
            return_value={
                'id': self.github_id,
            }
        )

        result_user = backend.authenticate(None, self.github_code)

        self.assertEqual(self.test_user, result_user)

    def test_authenticate_fail(self):
        """
        Test the authenticate() method if it fails.
        """

        backend = GithubOAuthBackend()

        backend.get_github_info = mock.MagicMock(
            return_value={
                'id': self.github_id + 1,
            }
        )

        result_user = backend.authenticate(None, self.github_code)

        self.assertIsNone(result_user)

    def test_authenticate_exception(self):
        """
        Test the authenticate() method if an exception is thrown.
        """

        backend = GithubOAuthBackend()

        backend.get_github_info = mock.MagicMock(
            side_effect=KeyError
        )

        result_user = backend.authenticate(None, self.github_code)

        self.assertIsNone(result_user)

    def test_get_user_success(self):
        """
        Test get_user method if it succeeds.
        """

        backend = GithubOAuthBackend()
        result_user = backend.get_user(self.test_user.id)

        self.assertEqual(result_user, self.test_user)

    def test_get_user_fail(self):
        """
        Test get_user method if it fails.
        """

        backend = GithubOAuthBackend()
        result_user = backend.get_user(self.test_user.id + 1)

        self.assertIsNone(result_user)

    @mock.patch('requests.post')
    def test__get_access_token(self, mock_post):
        """
        Test _get_access_token method.
        """

        mock_response = mock.Mock()
        mock_response.json.return_value = {
            'access_token': self.github_access_token,
            'token_type': 'bearer',
            'scope': 'user:email',
        }
        mock_post.return_value = mock_response

        access_token = GithubOAuthBackend._get_access_token(self.github_code)

        self.assertEqual(access_token, self.github_access_token)

    @mock.patch('requests.post', side_effect=RequestException)
    def test__get_access_token_exception_requests(self, mock_post):
        """
        Test _get_access_token method.
        """

        access_token = GithubOAuthBackend._get_access_token(self.github_code)

        self.assertIsNone(access_token)

    @mock.patch('requests.post')
    def test__get_access_token_exception_json(self, mock_post):
        """
        Test _get_access_token method.
        """

        mock_response = mock.Mock()
        mock_response.json.side_effect = ValueError
        mock_post.return_value = mock_response

        github_info = GithubOAuthBackend._get_access_token(
            self.github_code
        )

        self.assertIsNone(github_info)

    @mock.patch('requests.get')
    def test_get_github_info(self, mock_get):
        """
        Test _get_github_info method.
        """

        backend = GithubOAuthBackend()

        backend._get_access_token = mock.Mock(
            return_value=self.github_access_token
        )

        mock_response = mock.Mock()
        mock_response.json.return_value = {
            'login': self.github_username,
            'id': self.github_id
        }

        mock_get.return_value = mock_response

        github_info = backend.get_github_info(
            self.github_code
        )

        self.assertEqual(github_info, mock_response.json.return_value)

    def test_get_github_info_none(self):
        """
        Test _get_github_info method if access token is None.
        """

        backend = GithubOAuthBackend()

        backend._get_access_token = mock.Mock(
            return_value=None
        )

        github_info = backend.get_github_info(
            self.github_code
        )

        self.assertIsNone(github_info)

    @mock.patch('requests.get', side_effect=RequestException)
    def test_get_github_info_exception_requests(self, mock_get):
        """
        Test _get_github_info method if RequestException is raised.
        """

        backend = GithubOAuthBackend()
        backend._get_access_token = mock.Mock(
            return_value=self.github_access_token
        )

        github_info = backend.get_github_info(
            self.github_code
        )

        self.assertIsNone(github_info)

    @mock.patch('requests.get')
    def test_get_github_info_exception_json(self, mock_get):
        """
        Test _get_github_info method if ValueError is raised.
        """

        mock_response = mock.Mock()
        mock_response.json.side_effect = ValueError
        mock_get.return_value = mock_response

        backend = GithubOAuthBackend()
        backend._get_access_token = mock.Mock(
            return_value=self.github_access_token
        )

        github_info = backend.get_github_info(
            self.github_code
        )

        self.assertIsNone(github_info)
