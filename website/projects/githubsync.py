from datetime import datetime, timedelta

from django.conf import settings

from github import Github, GithubException, GithubIntegration


class GitHubAPITalker:
    """Communicate with GitHub API v3."""

    _access_token = None  # token to use when talking to github
    _github = Github()  # used to talk to GitHub as our own app
    _organization = None  # the organization to sync with

    _gi = GithubIntegration(settings.DJANGO_GITHUB_SYNC_APP_ID, settings.DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY)
    installation_id = settings.DJANGO_GITHUB_SYNC_APP_INSTALLATION_ID
    organization_name = settings.DJANGO_GITHUB_SYNC_ORGANIZATION_NAME

    @property
    def github_service(self):
        """Get a valid Github service instance (API endpoint) to make calls to."""
        self.renew_access_token_if_required()
        return self._github

    @property
    def github_organization(self):
        """Get a valid Github Organization to make calls to."""
        self.renew_access_token_if_required()
        return self._organization

    def renew_access_token_if_required(self):
        """
        Renew an access token if expired or not present.

        An access token must be created for all requests to authenticate.
        Access tokens are valid for only 10 minutes and must be recreated afterwards. A timedelta of 60 seconds is used
        to renew access tokens that are not longer than 60 seconds valid. Hence, all methods that require the access
        token are assumed to not take longer than 60 seconds.
        Also set the organization to use while syncing.

        :except: GithubException when requesting a new access token fails
        """
        if self._access_token is None or self._access_token.expires_at < datetime.utcnow() + timedelta(seconds=60):
            self._access_token = self._gi.get_access_token(self.installation_id)
            self._github = Github(self._access_token.token)
            self._organization = self._github.get_organization(self.organization_name)

    def create_team(self, project):
        """
        Create a team in GitHub for a project.

        :param project: the project for which a team must be created
        :return: the GitHub team that is created
        """
        github_team = self.github_organization.create_team(
            project.name, description=project.generate_team_description(), privacy="closed"
        )
        return github_team

    def update_team(self, project):
        """
        Update a team in GitHub for a project.

        :param project: the project for which a team must be updated
        """
        github_team = self.github_organization.get_team(project.github_team_id)
        if github_team.name != project.name or github_team.description != project.generate_team_description():
            github_team.edit(name=project.name, description=project.generate_team_description())

    def create_repo(self, repo):
        """
        Create a repository in GitHub.

        :param repo: The repository to create
        :return: the GitHub repository that is created
        """
        github_repo = self.github_organization.create_repo(
            name=repo.name,
            private=settings.DJANGO_GITHUB_SYNC_REPO_PRIVATE,
            # TODO: ask client if more settings are desired, or we maybe want to use a repo template
            # For some reason, adding the team directly by setting team_id does not work
        )

        github_team = self.github_organization.get_team(repo.project.github_team_id)
        github_team.add_to_repos(github_repo)
        github_team.set_repo_permission(github_repo, "admin")
        return github_repo

    def update_repo(self, repo):
        """
        Update a repository in GitHub.

        :param repo: the repository that must be updated
        """
        github_repo = self.github_service.get_repo(repo.github_repo_id)
        github_team = self.github_organization.get_team(repo.project.github_team_id)

        if not github_team.has_in_repos(github_repo):
            github_team.add_to_repos(github_repo)

        if not github_team.get_repo_permission(github_repo).admin:
            github_team.set_repo_permission(github_repo, "admin")

        if github_repo.name != repo.name:
            github_repo.edit(name=repo.name)

        # TODO: maybe (?) all other teams with access must be removed

    def sync_team_member(self, employee, project):
        """
        Add a employee to a GitHub team for a project, if not already in the team.

        :param employee: The employee to add
        :param project: The project to add the employee to
        :return: True if a the employee is newly invited
        """
        assert employee in project.get_employees()

        github_team = self.github_organization.get_team(project.github_team_id)

        github_employee = self.github_service.get_user(employee.github_username)
        if not github_team.has_in_members(github_employee):
            github_team.add_membership(github_employee, role="member")
            return True
        return False

    def remove_users_not_in_team(self, project):
        """
        Remove all GitHub users from a GitHub team that are not employees of a project.

        :param project: The project to use
        :return: The number of users removed, a list of users that could not be removed
        """
        users_removed = 0
        errors_removing = []

        github_team = self.github_organization.get_team(project.github_team_id)
        employee_list = [r[0] for r in project.get_employees().values_list("github_username")]

        for github_user in github_team.get_members():
            if github_user.login not in employee_list:
                try:
                    if (
                        not github_user.get_organization_membership(self.github_organization).role == "admin"
                    ):  # Prevent removing organization owners
                        self.github_organization.remove_from_members(github_user)
                    else:
                        github_team.remove_membership(github_user)
                    users_removed += 1
                except GithubException:
                    errors_removing.append(github_user.login)

        return users_removed, errors_removing

    def remove_team(self, project):
        """Remove a team for a project from GitHub and remove all employees of the project from the organization."""
        github_team = self.github_organization.get_team(project.github_team_id)

        for github_user in github_team.get_members():
            if (
                not github_user.get_organization_membership(self.github_organization).role == "admin"
            ):  # Prevent removing organization owners
                self.github_organization.remove_from_members(github_user)
        github_team.delete()

    def archive_repo(self, repo):
        """Archive a repository and return whether it is archived (True) or was already archived (False)."""
        github_repo = self.github_service.get_repo(repo.github_repo_id)
        if not github_repo.archived:
            github_repo.edit(archived=True)
            return True
        return False

    def username_exists(self, username):
        """Check if username is an existing Github username."""
        try:
            self._github.get_user(username)
            return True
        except GithubException:
            return False


talker = GitHubAPITalker()
