from admin_auto_filters.filters import AutocompleteFilter

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import path

from mailing_lists.models import MailingList

from projects.forms import ProjectAdminForm
from projects.githubsync import GitHubSync
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

    readonly_fields = ("github_repo_id",)

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)

    def get_extra(self, request, obj=None, **kwargs):
        """Only show an extra empty repository inline if no other repos exist."""
        return 0 if obj else 1


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
                    address=address,
                    description=f"Mailinglist '{address}@{settings.GSUITE_DOMAIN}' for  GiPHouse project"
                    f" '{project.name}' in the '{project.semester}' semester",
                )

                mailing_list.projects.add(project)

                messages.success(
                    request,
                    "Successfully created mailing list "
                    + mailing_list.address
                    + f"@{settings.GSUITE_DOMAIN} for "
                    + project.name,
                )
            except ValidationError:
                messages.error(
                    request,
                    "Could not create mailing list for "
                    + project.name
                    + ", this project already has the mailing list: "
                    + address,
                )

    def synchronise_to_GitHub(self, request, queryset):
        """Synchronise projects to GitHub."""
        sync = GitHubSync(queryset)
        task = sync.perform_asynchronous_sync()
        return redirect("admin:progress_bar", task=task)

    synchronise_to_GitHub.short_description = "Synchronise selected projects to GitHub"

    def synchronise_all_projects_to_GitHub(self, request):
        """Synchronise all project(teams) to GitHub."""
        return self.synchronise_to_GitHub(request, Project.objects.all())
        # TODO: it might become a problem if we keep doing this for all projects, since this set will get increasingly
        #  large. However only doing it for unarchived projects does not work either, since we would then not delete
        #  and archive anything ever. There are multiple solutions to this...
        # TODO: check for teams that shouldn't be there and remove them

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
