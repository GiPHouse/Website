from unittest import mock

from django.test import TestCase, Client
from django.contrib.auth.models import User


class CallbackTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create_user(
            username='test_user',
        )
        cls.test_user.backend = ''

    def setUp(self):
        self.client = Client()

    @mock.patch('github_oauth.views.authenticate')
    def test_login_get_success(self, mock_auth):
        """
    Test callback if authenticate succeeds.
        """
        mock_auth.return_value = self.test_user

        response = self.client.get('/oauth/login/?code=fakecode')

        self.assertRedirects(response, '/')

    @mock.patch('github_oauth.views.authenticate')
    def test_login_get_fail(self, mock_auth):
        """
        Test callback if authenticate fails.
        """
        mock_auth.return_value = None

        response = self.client.get('/oauth/login/?code=fakecode')

        self.assertRedirects(response, '/')

    def test_login_get_no_params(self):
        """
        Test callback view if GET request is made without parameters.
        """
        response = self.client.get('/oauth/')
        self.assertEqual(response.status_code, 404)

    def test_login_post(self):
        """
        Test callback view if non GET request is made.
        """

        response = self.client.post('/oauth/login/')
        self.assertEqual(response.status_code, 405)
