import csv
import zipfile
from io import BytesIO, StringIO

from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path

from github import GithubException

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


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Custom admin for projects."""

    form = ProjectAdminForm
    list_filter = [ProjectAdminClientFilter, ProjectAdminSemesterFilter]
    actions = ["export_addresses_csv", "synchronise_to_GitHub"]

    search_fields = ("name",)

    def export_addresses_csv(self, request, queryset):
        """Export the selected projects as email CSV zip."""
        zip_content = BytesIO()
        with zipfile.ZipFile(zip_content, "w") as zip_file:

            for project in queryset:
                content = StringIO()
                writer = csv.writer(content, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
                writer.writerow(
                    ["Group Email [Required]", "Member Email", "Member Name", "Member Role", "Member Type"]
                )

                for user in User.objects.filter(registration__project=project):
                    writer.writerow([project.email, user.email, "Member", "MEMBER", "USER"])

                zip_file.writestr(project.email + ".csv", content.getvalue())

        response = HttpResponse(zip_content.getvalue(), content_type="application/x-zip-compressed")
        response["Content-Disposition"] = "attachment; filename=" + "project-addresses-export.zip"
        return response

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
            except GithubException or AssertionError:
                messages.error(request, f"Something went wrong creating the project team for '{project_team}'.")
        else:
            try:
                github.update_team(project_team)  # if this fails, we might have a problem with the github_team_id
            except GithubException or AssertionError:
                messages.error(request, f"Something went wrong syncing the project team for '{project_team}'.")
                # TODO: If the exception is that the github team is not found, someone removed the team manually
                #  from GitHub and we maybe want to create the team again and save a new team_id, or someone
                #  changed the team_id in Django to a non-existing one. Or just notify the user and let them do
                #  this themselves

        for employee in project_team.get_employees():
            try:
                members_invited += github.sync_team_member(employee, project_team)
            except GithubException or AssertionError:
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
        except GithubException or AssertionError:
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
                except GithubException or AssertionError:
                    messages.error(
                        request, f"Something went wrong creating repository '{project_repo}' for '{project_team}'."
                    )
            else:
                try:
                    github.update_repo(project_repo)  # if this fails, we might have a problem with the github_repo_id
                except GithubException or AssertionError:
                    messages.error(
                        request, f"Something went wrong syncing the repository '{project_repo}' for '{project_team}'.",
                    )
        return new_repos_created

    def synchronise_to_GitHub(self, request, queryset):
        """Synchronise projects to GitHub."""
        new_teams_created = 0
        new_repos_created = 0
        total_invited = 0
        total_removed = 0

        for project_team in queryset:
            team_created, members_invited, users_removed = self.create_or_update_team(request, project_team)
            if team_created:
                new_teams_created += 1
            total_invited += members_invited
            total_removed += users_removed

            new_repos_created += self.create_or_update_repos(request, project_team)

        # TODO: maybe improve error handling and success messages

        messages.success(
            request,
            f"A total of {new_teams_created} teams and {new_repos_created} repositories have been created, a total of "
            f"{total_invited} employees have been invited to their teams and a total of "
            f"{total_removed} users have been removed from GitHub teams.",
        )

    synchronise_to_GitHub.short_description = "Synchronise selected projects to GitHub"

    def synchronise_all_projects_to_GitHub(self, request):
        """Synchronise all project(teams) to GitHub."""
        self.synchronise_to_GitHub(request, Project.objects.all())
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


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Custom admin for clients."""

    search_fields = ("name",)


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    """Custom admin for repositories."""
