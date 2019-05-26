from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.test import Client, RequestFactory, TestCase

from github_oauth.backends import GithubOAuthError
from github_oauth.views import BaseGithubView, GithubRegisterView

from registrations.models import GiphouseProfile

User: DjangoUser = get_user_model()


class LoginTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.test_user_password = 'password'

        cls.test_user = User.objects.create_user(
            username='test_user',
            password=cls.test_user_password
        )
        cls.test_user.backend = ''

    def setUp(self):
        self.client = Client()
        self.request_factory = RequestFactory()

    def test_base_get(self):
        """Test GET request for base class."""

        request = self.request_factory.get('/?code=fakecode')
        request.user = AnonymousUser()

        response = BaseGithubView.as_view()(request)
        self.assertRedirects(response, BaseGithubView.redirect_url_success, fetch_redirect_response=False)

    @mock.patch('github_oauth.views.authenticate')
    def test_login_get_success(self, mock_auth):
        """
        Test login if authenticate succeeds.
        """
        mock_auth.return_value = self.test_user

        response = self.client.get('/oauth/login/?code=fakecode')

        self.assertRedirects(response, reverse('home'))

    @mock.patch('github_oauth.views.authenticate')
    def test_login_get_fail(self, mock_auth):
        """
        Test login if authenticate fails.
        """
        mock_auth.return_value = None

        response = self.client.get('/oauth/login/?code=fakecode')

        self.assertRedirects(response, reverse('home'))

    def test_login_get_no_params(self):
        """
        Test login view if GET request is made without parameters.
        """
        response = self.client.get('/oauth/login/')
        self.assertEqual(response.status_code, 400)

    def test_login_post(self):
        """
        Test login view if non GET request is made.
        """

        response = self.client.post('/oauth/login/?code=fakecode')
        self.assertEqual(response.status_code, 405)

    def test_login_authenticated(self):
        """
        Test login view if user is authenticated.
        """

        self.client.login(
            username=self.test_user.username,
            password=self.test_user_password,
        )

        response = self.client.get('/oauth/login/?code=fakecode')

        self.assertRedirects(response, reverse('home'))


class RegisterTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.github_id = 0

        cls.test_user_password = 'password'

        cls.test_user = User.objects.create_user(
            username='test_user',
            password=cls.test_user_password
        )
        cls.test_user.backend = ''

        cls.giphouse_profile = GiphouseProfile.objects.create(
            user=cls.test_user,
            github_username='test_user',
            github_id=cls.github_id,
        )

    def setUp(self):
        self.client = Client()

    @mock.patch('github_oauth.backends.GithubOAuthBackend.get_github_info')
    def test_register(self, mock_get_github_info):
        """
        Test register view.
        """

        mock_get_github_info.return_value = {
            'id': self.github_id + 1,
            'email': None,
            'login': None,
            'name': None,
        }

        response = self.client.get('/oauth/register/?code=fakecode')

        self.assertRedirects(response, reverse('registrations:step2'))

    @mock.patch('github_oauth.backends.GithubOAuthBackend.get_github_info')
    def test_register_user_exists(self, mock_get_github_info):
        """
        Test register view if user already exists.
        """

        mock_get_github_info.return_value = {
            'id': self.github_id,
        }

        response = self.client.get('/oauth/register/?code=fakecode')
        self.assertRedirects(response, reverse('home'))

    def test_login_get_no_params(self):
        """
        Test register view if GET request is made without parameters.
        """
        response = self.client.get('/oauth/register/')
        self.assertEqual(response.status_code, 400)

    def test_register_post(self):
        """
        Test register view if non GET request is made.
        """

        response = self.client.post('/oauth/register/?code=fakecode')
        self.assertEqual(response.status_code, 405)

    def test_register_authenticated(self):
        """
        Test register view if user is authenticated.
        """

        self.client.login(
            username=self.test_user.username,
            password=self.test_user_password,
        )

        response = self.client.get('/oauth/register/?code=fakecode')

        self.assertRedirects(response, reverse('home'))

    @mock.patch('github_oauth.backends.GithubOAuthBackend.get_github_info', side_effect=GithubOAuthError)
    def test_register_github_fail(self, mock_get_github_info):

        response = self.client.get('/oauth/register/?code=fakecode', follow=True)

        self.assertContains(response, GithubOAuthError.__doc__)
        self.assertRedirects(response, GithubRegisterView.redirect_url_failure)

    @mock.patch('github_oauth.backends.GithubOAuthBackend.get_github_info', side_effect=GithubOAuthError('Error!'))
    def test_register_github_fail_custom_message(self, mock_get_github_info):

        response = self.client.get('/oauth/register/?code=fakecode', follow=True)

        self.assertContains(response, 'Error!')
        self.assertRedirects(response, GithubRegisterView.redirect_url_failure)
