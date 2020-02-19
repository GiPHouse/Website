import datetime

from django.conf import settings

from github import Github, GithubIntegration


class GitHubAPITalker:
    """Communicate with GitHub API v3."""

    github = None  # used to talk to GitHub as our own app
    access_token = None
    gi = GithubIntegration(settings.GITHUB_APP_ID, settings.GITHUB_APP_PRIVATE_KEY)
    organization_name = settings.GITHUB_ORGANIZATION_NAME
    installation_id = settings.GITHUB_APP_INSTALLATION_ID

    def __init__(self):
        """On initialization, get a first access token and get the organization to use."""
        self.renew_access_token_if_required()
        self.organization = self.github.get_organization(self.organization_name)

    def renew_access_token_if_required(self):
        """
        Renew an access token if expired or not present.

        An access token must be created for all requests to authenticate.
        Access tokens are valid for only 10 minutes and must be recreated afterwards.

        :except: GithubException when requesting a new access token fails
        """
        if self.access_token is None or self.access_token.expires_at < datetime.datetime.now():
            self.access_token = self.gi.get_access_token(self.installation_id)
            self.github = Github(self.access_token.token)


talker = GitHubAPITalker()
