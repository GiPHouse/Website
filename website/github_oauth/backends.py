import requests
from requests.exceptions import RequestException

from django.contrib.auth import get_user_model
from django.conf import settings

from .links import URL_GITHUB_ACCESS_TOKEN, URL_GITHUB_USER_INFO

User = get_user_model()


class GithubOAuthBackend:

    def authenticate(self, request, code):
        """
        This will try to request an access token from GitHub using OAuth
        and authenticate an user.
        :param request: The request made.
        :param code: The code needed to request the access token.
        :return: The authenticated user or None.
        """

        try:
            github_id = self.get_github_info(code)['id']
        except (RequestException, ValueError, KeyError):
            return None

        return self.github_authenticate(github_id)

    @staticmethod
    def github_authenticate(github_id):
        try:
            return User.objects.get(giphouseprofile__github_id=github_id)
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        """
        Retrieve an user.
        :param user_id: Primary key of user.
        :return: User if found else None.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_access_token(code):
        """
        Request access token through GitHub OAuth API.
        :param code: The code needed to request the access token.
        :return: GitHub OAuth access token.
        """
        response = requests.post(
            URL_GITHUB_ACCESS_TOKEN,
            data={
                'client_id': settings.GITHUB_CLIENT_ID,
                'client_secret': settings.GITHUB_CLIENT_SECRET,
                'code': code,
            },
            headers={
                'Accept': 'application/json'
            },
        )
        return response.json()['access_token']

    @classmethod
    def get_github_info(cls, code):
        """
        Retrieve GitHub username and user id through GitHub API.
        :param code: The code needed to request the access token.
        :return: A dictionary with GitHub user information
        """
        access_token = cls.get_access_token(code)

        response = requests.get(
            URL_GITHUB_USER_INFO,
            params={
                'access_token': access_token
            },
            headers={
                'Accept': 'application/json'
            },
        )

        github_info = response.json()
        return github_info
