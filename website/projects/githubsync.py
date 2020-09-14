import logging
import threading
from datetime import datetime, timedelta

from django.conf import settings
from django.urls import reverse

from github import Github, GithubException, GithubIntegration, UnknownObjectException

from projects.models import ProjectToBeDeleted, Repository, RepositoryToBeDeleted

from tasks.models import Task


class GitHubAPITalker:
    """Communicate with GitHub API v3."""

    _access_token = None  # token to use when talking to github
    _github = Github()  # used to talk to GitHub as our own app
    _organization = None  # the organization to sync with

    _gi = GithubIntegration(settings.DJANGO_GITHUB_SYNC_APP_ID, settings.DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY)
    _logger = logging.getLogger("django.github")
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

    def create_repo(self, repo):
        """
        Create a repository in GitHub for a project.

        :param repo: the repository object for which a GitHub repository must be created
        :return: the GitHub repository that is created
        """
        return self.github_organization.create_repo(name=repo.name, private=repo.private)

    def get_team(self, team_id):
        """Get a team from the GiPHouse GitHub organization."""
        return self.github_organization.get_team(team_id)

    def get_user(self, username):
        """Get a user from GitHub."""
        return self.github_service.get_user(username)

    def get_role_of_user(self, user):
        """Get the role of a user in the GiPHouse GitHub organization."""
        return user.get_organization_membership(self.github_organization).role

    def get_repo(self, repo_id):
        """Get a repo from GitHub."""
        return self.github_service.get_repo(repo_id)

    def remove_user(self, user):
        """Remove a user from the GiPHouse GitHub organization."""
        self.github_organization.remove_from_members(user)


class GitHubSync:
    """Sync with GitHub."""

    def __init__(self, projects):
        """
        Create a GitHub Sync with given projects.

        :param projects: An iterable of all projects that should be synced
        """
        self.projects = projects
        self.logger = logging.getLogger("django.github")
        self.fail = False
        self.teams_created = 0
        self.repos_created = 0
        self.repos_archived = 0
        self.users_invited = 0
        self.users_removed = 0
        self.github = talker
        self.task = Task.objects.create(
            total=len(self.projects), completed=0, redirect_url=reverse("admin:projects_project_changelist")
        )

    def error(self, msg):
        """Log an error message and set the fail state to True."""
        self.logger.error(msg)
        self.fail = True

    def warning(self, msg):
        """Log a warning message."""
        self.logger.warning(msg)

    def info(self, msg):
        """Log an info message."""
        self.logger.info(msg)

    def sync_team_member(self, employee, project):
        """
        Add a employee to a GitHub team for a project, if not already in the team.

        :param employee: The employee to add
        :param project: The project to add the employee to
        :return: True if a the employee is newly invited
        """
        if employee in project.get_employees():

            github_team = self.github.get_team(project.github_team_id)

            github_employee = self.github.get_user(employee.github_username)
            if not github_team.has_in_members(github_employee):
                github_team.add_membership(github_employee, role="member")
                self.users_invited += 1
                self.info(f"Invited {employee.get_full_name()} to team {github_team.name}")
                return True
        return False

    def create_or_update_team(self, project_team):
        """
        Create a GitHub team for a project, or update it if already existing.

        If a github_team_id is None, a new team is created and saved, otherwise the team is updated.

        :param project_team: The team to create or update the team for
        """
        if project_team.github_team_id is None:
            try:
                project_team.github_team_id = self.github.create_team(project_team).id
                self.info(f"Created team {project_team.name}")
                self.teams_created += 1
                project_team.save()
            except (GithubException, AssertionError):
                self.error(f"Something went wrong creating the project team for '{project_team}'.")
        else:
            try:
                self.update_team(project_team)  # if this fails, we might have a problem with the github_team_id
            except (GithubException, AssertionError):
                self.error(
                    f"Something went wrong syncing the project team for '{project_team}'. Does the "
                    f"github_team_id still belong to a valid team on GitHub?"
                )

        for employee in project_team.get_employees():
            try:
                self.sync_team_member(employee, project_team)
            except (GithubException, AssertionError):
                self.error(f"Something went wrong syncing {employee} with the GitHub team for '{project_team}'.")

        try:
            self.remove_users_not_in_team(project_team)
        except (GithubException, AssertionError):
            self.error(f"Something went wrong while removing unwanted users from GitHub team for '{project_team}'.")

    def remove_users_not_in_team(self, project):
        """
        Remove all GitHub users from a GitHub team that are not employees of a project.

        :param project: The project to use
        """
        github_team = self.github.get_team(project.github_team_id)
        employee_list = [r[0] for r in project.get_employees().values_list("github_username")]

        for github_user in github_team.get_members():
            if github_user.login not in employee_list:
                try:
                    if self.github.get_role_of_user(github_user) != "admin":  # Prevent removing organization owners
                        self.github.remove_user(github_user)
                        self.info(f"Removed {github_user.name} from team {github_team.name} and the organization.")
                    else:
                        github_team.remove_membership(github_user)
                        self.info(
                            f"Removed {github_user.name} from team {github_team.name} but not from the organization, "
                            f"because {github_user.name} is an admin"
                        )
                    self.users_removed += 1
                except GithubException:
                    self.error(f"Something went wrong while removing {github_user.name} from team {github_team.name}")

    def remove_team(self, project):
        """Remove a team for a project from GitHub and remove all employees of the project from the organization."""
        github_team = self.github.get_team(project.github_team_id)

        for github_user in github_team.get_members():
            if self.github.get_role_of_user(github_user) != "admin":  # Prevent removing organization owners
                try:
                    self.github.remove_user(github_user)
                    self.users_removed += 1
                    self.info(f"Removed {github_user.name} from the organization")
                except GithubException:
                    self.error(f"Something went wrong while removing {github_user.name} from team {github_team.name}")
        try:
            github_team.delete()
            self.info(f"Removed team {github_team.name}")
        except GithubException:
            self.error(f"Something went wrong while removing team {github_team.name}")

    def archive_repo(self, repo):
        """Archive a repository and return whether it is archived (True) or was already archived (False)."""
        github_repo = self.github.get_repo(repo.github_repo_id)
        if not github_repo.archived:
            github_repo.edit(archived=True)
            self.info(f"Archived repository {github_repo.name}")
            self.repos_archived += 1
            return True
        return False

    def archive_project(self, project_team):
        """
        Archive a project by deleting the team and removing the employees.

        :param project_team: The project to archive
        """
        if project_team.github_team_id is not None:
            try:
                self.remove_team(project_team)
                project_team.github_team_id = None
                project_team.save()
            except (GithubException, AssertionError):
                self.error(f"Something went wrong removing the GitHub team for '{project_team}'.")
        else:
            self.warning(f"Project team {project_team} was not archived, because it does not exist on GitHub either.")

    def update_repo(self, repo):
        """
        Update a repository in GitHub.

        :param repo: the repository that must be updated
        """
        github_repo = self.github.get_repo(repo.github_repo_id)
        github_team = self.github.get_team(repo.project.github_team_id)

        if not github_team.has_in_repos(github_repo):
            github_team.add_to_repos(github_repo)
            self.info(f"Added team {github_team.name} to repository {github_repo.name}")

        if not github_team.get_repo_permission(github_repo).admin:
            github_team.set_repo_permission(github_repo, "admin")
            self.info(f"Gave admin permissions to team {github_team.name} for repository {github_repo.name}")

        if github_repo.name != repo.name:
            old_name = github_repo.name
            github_repo.edit(name=repo.name)
            self.info(f"Changed name of repository {old_name} to {github_repo.name}")

        if github_repo.private != repo.private:
            github_repo.edit(private=repo.private)
            self.info(f"Changed privacy of repository {github_repo.name} to {'private' if repo.private else 'public'}")

    def create_or_update_repos(self, project_team):
        """
        Create GitHub repositories for a project, or update the repository if already existing.

        If a github_repo_id is None, a new repo is created and saved, otherwise the repo is updated.

        :param project_team: The team to create or update the repos for
        """
        for project_repo in Repository.objects.filter(project=project_team):
            if project_repo.github_repo_id is None:
                try:
                    project_repo.github_repo_id = self.github.create_repo(project_repo).id
                    project_repo.save()
                    self.info(f"Created repository {project_repo}")
                    self.repos_created += 1
                except (GithubException, AssertionError):
                    self.error(f"Something went wrong creating repository '{project_repo}' for '{project_team}'.")
            else:
                try:
                    self.update_repo(project_repo)  # if this fails, we might have a problem with the github_repo_id
                except (GithubException, AssertionError):
                    self.error(f"Something went wrong syncing the repository '{project_repo}' for '{project_team}'.")

    def update_team(self, project):
        """
        Update a team in GitHub for a project.

        :param project: the project for which a team must be updated
        """
        github_team = self.github.get_team(project.github_team_id)
        if github_team.name != project.name or github_team.description != project.generate_team_description():
            github_team.edit(name=project.name, description=project.generate_team_description())
            self.info(f"Updated name and description of team {project.name}")
            return True
        return False

    def create_repo(self, repo):
        """
        Create a repository in GitHub.

        :param repo: The repository to create
        :return: the GitHub repository that is created
        """
        github_repo = self.github.create_repo(repo)
        self.info(f"Created repository {repo.name}")
        github_team = self.github.get_team(repo.project.github_team_id)
        github_team.add_to_repos(github_repo)
        github_team.set_repo_permission(github_repo, "admin")
        self.info(f"Added team {github_team.name} to repository {repo.name}")
        return github_repo

    def archive_repos_marked_as_archived(self, project_team):
        """Archive all repos of this project that are marked as archived."""
        for project_repo in Repository.objects.filter(project=project_team):
            if project_repo.is_archived == Repository.Archived.PENDING:
                try:
                    if project_repo.github_repo_id is not None:
                        self.archive_repo(project_repo)
                    else:
                        self.warning(
                            f"Repository {project_repo} was not archived, because it does not exist on GitHub either."
                        )
                    project_repo.is_archived = Repository.Archived.CONFIRMED
                    project_repo.save()
                except (GithubException, AssertionError):
                    self.error(f"Something went wrong archiving the repository '{project_repo}'.")

    def sync_project(self, project):
        """Sync one project to GitHub."""
        if project.is_archived == Repository.Archived.NOT_ARCHIVED:
            self.create_or_update_team(project)
            self.create_or_update_repos(project)
            self.archive_repos_marked_as_archived(project)
        elif project.is_archived == Repository.Archived.PENDING:
            self.archive_repos_marked_as_archived(project)
            self.archive_project(project)

    def delete_teams_and_repos_to_be_deleted(self):
        """Remove all repositories and teams deleted in Django of which the id's are stored for deletion."""
        for repo in RepositoryToBeDeleted.objects.all():
            try:
                self.archive_repo(repo)
            except UnknownObjectException:
                self.error(
                    f"Something went wrong removing orphan GitHub repository with id {repo.github_repo_id}'. "
                    f"Maybe it was already deleted manually?"
                )
            except (GithubException, AssertionError):
                self.error(
                    f"Something went wrong archiving orphan GitHub repository with id {repo.github_repo_id}'. "
                    f"Will try again at next sync."
                )
                continue
            repo.delete()

        for team in ProjectToBeDeleted.objects.all():
            try:
                self.remove_team(team)
            except UnknownObjectException:
                self.error(
                    f"Something went wrong removing orphan GitHub team with id {team.github_team_id}'."
                    f"Maybe it was already deleted manually?"
                )
            except (GithubException, AssertionError):
                self.error(
                    f"Something went wrong removing orphan GitHub team with id {team.github_team_id}'. "
                    f"Will try again at next sync."
                )
                continue
            team.delete()

    def perform_sync(self):
        """Sync all selected projects to GitHub."""
        try:
            self.delete_teams_and_repos_to_be_deleted()
        except Exception as e:
            self.logger.exception(e)
            self.fail = True
        for project in self.projects:
            try:
                self.sync_project(project)
            except Exception as e:
                self.logger.exception(e)
                self.fail = True
            self.task.completed += 1
            self.task.save()
        self.task.fail = self.fail

        self.task.success_message = (
            f"A total of {self.teams_created} teams and {self.repos_created} repositories have been created, "
            f"a total of {self.users_invited} employees have been invited to their teams and "
            f"a total of {self.users_removed} users have been removed from GitHub teams. "
            f"{self.repos_archived} repositories have been archived."
        )
        self.task.save()

    def perform_asynchronous_sync(self):
        """Sync all selected projects to GitHub asynchronously."""
        thread = threading.Thread(target=self.perform_sync)
        thread.start()
        return self.task.id


talker = GitHubAPITalker()
