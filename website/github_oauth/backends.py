from django.conf import settings
from django.contrib.auth import get_user_model

import requests
from requests.exceptions import RequestException

from github_oauth.links import URL_GITHUB_ACCESS_TOKEN, URL_GITHUB_USER_INFO

from registrations.models import Employee

User: Employee = get_user_model()


class GithubOAuthError(Exception):
    """Error encountered during Github OAuth."""

    def __str__(self):
        """Return the message or the docstring of the class if no message has been specified."""
        if self.args:
            return super().__str__()

        return self.__doc__


class GithubOAuthConnectionError(GithubOAuthError):
    """Error encountered during connection with Github OAuth."""


class GithubOAuthJSONDecodeError(GithubOAuthError):
    """Error decoding Github OAuth response."""


class GithubOAuthBadResponse(GithubOAuthError):
    """Bad response from Github OAuth."""


class GithubOAuthBackend:
    """Authentication backend using the GitHub OAuth provider."""

    def authenticate(self, request, code):
        """
        Request an access token from GitHub using OAuth and authenticate a user.

        :param request: The request made.
        :param code: The code needed to request the access token.
        :return: The authenticated user or None.
        """
        try:
            github_id = self.get_github_info(code)["id"]
        except KeyError:
            raise GithubOAuthBadResponse

        return self._get_giphouse_user(github_id)

    def get_github_info(self, code):
        """
        Retrieve GitHub username and user id through GitHub API.

        :param code: The code needed to request the access token.
        :return: A dictionary with GitHub user information
        """
        access_token = self._get_access_token(code)

        try:
            response = requests.get(
                URL_GITHUB_USER_INFO, params={"access_token": access_token}, headers={"Accept": "application/json"}
            )
        except RequestException:
            raise GithubOAuthConnectionError

        try:
            return response.json()
        except ValueError:
            raise GithubOAuthJSONDecodeError

    def get_user(self, user_id):
        """
        Retrieve a user.

        :param user_id: Primary key of user.
        :return: User if found else None.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def _get_giphouse_user(github_id):
        """
        Get user with github_id.

        :param github_id: GitHub id of required user.
        :return: A user with github_id as GitHub id or None.
        """
        try:
            return User.objects.get(github_id=github_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def _get_access_token(code):
        """
        Request access token through GitHub OAuth API.

        :param code: The code needed to request the access token.
        :return: GitHub OAuth access token.
        """
        try:
            response = requests.post(
                URL_GITHUB_ACCESS_TOKEN,
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
        except RequestException:
            raise GithubOAuthConnectionError

        try:
            return response.json()["access_token"]
        except ValueError:
            raise GithubOAuthJSONDecodeError
        except KeyError:
            raise GithubOAuthBadResponse
