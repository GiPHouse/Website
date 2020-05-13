from admin_auto_filters.filters import AutocompleteFilter

from django import forms
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


class ProjectAdminArchivedFilter(admin.SimpleListFilter):
    """Filter class to filter Projects on archived status."""

    title = "Has archived repositories"
    parameter_name = "repo_archived"

    def lookups(self, request, model_admin):
        """Get the values to filter on."""
        return (
            (1, True),
            (0, False),
        )

    def queryset(self, request, queryset):
        """Return the queryset required for the selected value."""
        return queryset.filter(repository__is_archived=self.value()).distinct()


class RepositoryInlineFormset(forms.models.BaseInlineFormSet):
    """Custom formset for projects and their repositories."""

    def clean(self):
        """Make sure a project has at least one repository."""
        repositories_left = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                repositories_left += 1
        if repositories_left < 1:
            raise forms.ValidationError("Projects must have at least one repository.")


class RepositoryInline(admin.StackedInline):
    """Inline form for Repository."""

    formset = RepositoryInlineFormset
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
    list_filter = [ProjectAdminClientFilter, ProjectAdminSemesterFilter, ProjectAdminArchivedFilter]
    list_display = ["name", "client", "is_archived", "number_of_repos"]

    actions = ["create_mailing_lists", "synchronise_to_GitHub", "archive_all_repositories"]
    inlines = [RepositoryInline]

    search_fields = ("name",)
    readonly_fields = ("github_team_id",)

    def is_archived(self, instance):
        """Return the archived status of a Project instance (required to display property as check mark)."""
        return instance.is_archived

    # Instruct Django admin to display is_archived as check mark
    is_archived.boolean = True
    is_archived.short_description = "Project archived"

    def archive_all_repositories(self, request, queryset):
        """Archive all the repositories for the selected projects."""
        for project in queryset:
            num_archived = Repository.objects.filter(is_archived=False, project=project).update(is_archived=True)
        messages.success(
            request, f"Succesfully archived {num_archived} repositories.",
        )

    def create_mailing_lists(self, request, queryset):
        """Create mailing lists for the selected projects."""
        for project in queryset:
            address = project.generate_email()

            try:
                mailing_list = MailingList.objects.create(
                    address=address,
                    description=f"Mailing list for project '{project.name}' in the '{project.semester}' semester.",
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
            "js/slugify.js",
            "js/repo_naming.js",
        )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Custom admin for clients."""

    search_fields = ("name",)
