import requests
from requests.exceptions import RequestException

from django.conf import settings
from django.contrib.auth.models import User

from registrations.models import GiPHouseProfile

from .links import URL_GITHUB_ACCESS_TOKEN, URL_GITHUB_USER_INFO


class GithubOAuthBackend:

    def authenticate(self, request, code):

        try:
            access_token = self._get_access_token(code)
            github_username, github_id = self._get_github_info(access_token)
            print(access_token, github_username, github_id)
        except (RequestException, ValueError, KeyError):
            return None

        try:
            user = User.objects.get(giphouseprofile__github_id=github_id)
        except (GiPHouseProfile.DoesNotExist, User.DoesNotExist):
            pass
        else:
            return user

        return self.get_user(1)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def _get_access_token(code):
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

    @staticmethod
    def _get_github_info(access_token):
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

        return github_info['login'], github_info['id']
