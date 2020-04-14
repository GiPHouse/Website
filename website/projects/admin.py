from admin_auto_filters.filters import AutocompleteFilter

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import path

from github import GithubException

from mailing_lists.models import MailingList

from projects import githubsync
from projects.forms import ProjectAdminForm
from projects.models import Client, Project, Repository

from registrations.models import Employee

User: Employee = get_user_model()


class ProjectAdminClientFilter(AutocompleteFilter):
    """Filter class to filter Client objects."""

    title = "Client"
    field_name = "client"


class ProjectAdminSemesterFilter(AutocompleteFilter):
    """Filter class to filter Semester objects."""

    title = "Semester"
    field_name = "semester"


class RepositoryInline(admin.StackedInline):
    """Inline form for Repository."""

    model = Repository
    extra = 1

    readonly_fields = ("github_repo_id",)

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Custom admin for projects."""

    form = ProjectAdminForm
    list_filter = [ProjectAdminClientFilter, ProjectAdminSemesterFilter]
    actions = ["create_mailing_lists", "synchronise_to_GitHub"]
    inlines = [RepositoryInline]

    search_fields = ("name",)
    readonly_fields = ("github_team_id",)

    def create_mailing_lists(self, request, queryset):
        """Create mailing lists for the selected projects."""
        for project in queryset:

            address = project.generate_email()
            try:
                mailing_list = MailingList.objects.create(
                    address=project.generate_email(),
                    description=f"Mailinglist '{address}@{settings.GSUITE_DOMAIN}' for  GiPHouse project"
                    f" '{project.name}' in the '{project.semester}' semester",
                )

                mailing_list.projects.add(project)

                messages.success(
                    request, "Successfully created mailing list " + mailing_list.address + " for " + project.name
                )
            except ValidationError:
                messages.error(
                    request,
                    "Could not create mailing list for "
                    + project.name
                    + ", this project already has the mailing list: "
                    + address,
                )

    def create_or_update_team(self, request, project_team):
        """
        Create a GitHub team for a project, or update it if already existing.

        If a github_team_id is None, a new team is created and saved, otherwise the team is updated.

        :param request: The request associated :param project_team: The team to create or update the team for
        :return: True if a new team is created, The number of newly invited team members, The number of removed
        GitHub users from a team.
        """
        github = githubsync.talker

        team_created = False
        members_invited = 0
        users_removed = 0

        if project_team.github_team_id is None:
            try:
                project_team.github_team_id = github.create_team(project_team).id
                project_team.save()
                team_created = True
            except (GithubException, AssertionError):
                messages.error(request, f"Something went wrong creating the project team for '{project_team}'.")
        else:
            try:
                github.update_team(project_team)  # if this fails, we might have a problem with the github_team_id
            except (GithubException, AssertionError):
                messages.error(request, f"Something went wrong syncing the project team for '{project_team}'.")
                # TODO: If the exception is that the github team is not found, someone removed the team manually
                #  from GitHub and we maybe want to create the team again and save a new team_id, or someone
                #  changed the team_id in Django to a non-existing one. Or just notify the user and let them do
                #  this themselves

        for employee in project_team.get_employees():
            try:
                members_invited += github.sync_team_member(employee, project_team)
            except (GithubException, AssertionError):
                messages.error(
                    request, f"Something went wrong syncing {employee} with the GitHub team for '{project_team}'."
                )

        try:
            users_removed, errors_removing = github.remove_users_not_in_team(project_team)
            if len(errors_removing) > 0:
                messages.error(
                    request,
                    f"Those users should be removed from GitHub team for '{project_team}' but could not be "
                    f"removed: {errors_removing}.",
                )
        except (GithubException, AssertionError):
            messages.error(
                request, f"Something went wrong removing unwanted users from GitHub team for '{project_team}'."
            )

        return team_created, members_invited, users_removed

    def create_or_update_repos(self, request, project_team):
        """
        Create GitHub repositories for a project, or update the repository if already existing.

        If a github_repo_id is None, a new repo is created and saved, otherwise the repo is updated.

        :param request: The request associated
        :param project_team: The team to create or update the repos for
        :return: The number of newly created repositories
        """
        github = githubsync.talker
        new_repos_created = 0

        for project_repo in Repository.objects.filter(project=project_team):
            if project_repo.github_repo_id is None:
                try:
                    project_repo.github_repo_id = github.create_repo(project_repo).id
                    project_repo.save()
                    new_repos_created += 1
                except (GithubException, AssertionError):
                    messages.error(
                        request, f"Something went wrong creating repository '{project_repo}' for '{project_team}'."
                    )
            else:
                try:
                    github.update_repo(project_repo)  # if this fails, we might have a problem with the github_repo_id
                except (GithubException, AssertionError):
                    messages.error(
                        request, f"Something went wrong syncing the repository '{project_repo}' for '{project_team}'.",
                    )
        return new_repos_created

    def archive_project(self, request, project_team):
        """Archive a project by deleting the team, removing the employees and archiving the repositories."""
        github = githubsync.talker
        repos_archived = 0

        for project_repo in Repository.objects.filter(project=project_team):
            try:
                if project_repo.github_repo_id is not None:
                    if github.archive_repo(project_repo):
                        repos_archived += 1
                else:
                    messages.warning(
                        request,
                        f"Repository {project_repo} was not archived, because it does not exist on GitHub either.",
                    )
            except (GithubException, AssertionError):
                messages.error(
                    request, f"Something went wrong archiving the repository '{project_repo}'.",
                )
        if project_team.github_team_id is not None:
            try:
                github.remove_team(project_team)
                project_team.github_team_id = None
                project_team.save()
            except (GithubException, AssertionError):
                messages.error(
                    request, f"Something went wrong removing the GitHub team for '{project_team}'.",
                )
        else:
            messages.warning(
                request, f"Project team {project_team} was not archived, because it does not exist on GitHub either.",
            )
        return repos_archived

    def synchronise_to_GitHub(self, request, queryset):
        """Synchronise projects to GitHub."""
        new_teams_created = 0
        new_repos_created = 0
        repos_archived = 0
        total_invited = 0
        total_removed = 0

        for project_team in queryset:
            if not project_team.is_archived:
                team_created, members_invited, users_removed = self.create_or_update_team(request, project_team)
                if team_created:
                    new_teams_created += 1
                total_invited += members_invited
                total_removed += users_removed

                new_repos_created += self.create_or_update_repos(request, project_team)
            else:
                repos_archived += self.archive_project(request, project_team)

        # TODO: maybe improve error handling and success messages

        messages.success(
            request,
            f"A total of {new_teams_created} teams and {new_repos_created} repositories have been created, a total of "
            f"{total_invited} employees have been invited to their teams and a total of "
            f"{total_removed} users have been removed from GitHub teams. {repos_archived} repositories have been "
            f"archived.",
        )

    synchronise_to_GitHub.short_description = "Synchronise selected projects to GitHub"

    def synchronise_all_projects_to_GitHub(self, request):
        """Synchronise all project(teams) to GitHub."""
        self.synchronise_to_GitHub(request, Project.objects.all())
        # TODO: it might become a problem if we keep doing this for all projects, since this set will get increasingly
        #  large. However only doing it for unarchived projects does not work either, since we would then not delete
        #  and archive anything ever. There are multiple solutions to this...
        # TODO: check for teams that shouldn't be there and remove them
        return redirect("/admin/projects/project")

    def get_urls(self):
        """Get admin urls."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync-to-github/",
                self.admin_site.admin_view(self.synchronise_all_projects_to_GitHub),
                name="synchronise_to_github",
            ),
        ]
        return custom_urls + urls

    class Media:
        """Necessary to use AutocompleteFilter."""

        js = (
            "js/jquery-3.4.1.slim.min.js",
            "js/repo_naming.js",
        )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Custom admin for clients."""

    search_fields = ("name",)
