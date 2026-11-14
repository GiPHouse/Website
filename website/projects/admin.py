import csv
from io import StringIO

from admin_auto_filters.filters import AutocompleteFilter

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import path
from django.utils.text import slugify

from github import Repository as GithubRepository
from github import UnknownObjectException, GithubException

from courses.models import Semester

from mailing_lists.models import MailingList

from projects.apps import ProjectsConfig
from projects.forms import (
    ProjectAdminForm,
    NewRepositoryInlineForm,
    ExistingRepositoryInlineForm,
)
from projects.githubsync import GitHubSync, GitHubAPITalker
from projects.models import (
    Client,
    Project,
    Repository,
    NewRepository,
    ExistingRepository,
)

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
        annotated = queryset.annotate(
            num_unarchived_repos=Count(
                "repository",
                filter=Q(
                    repository__is_archived=Repository.Archived.NOT_ARCHIVED
                ),
            )
        )
        if self.value() == "1":
            return annotated.filter(num_unarchived_repos=0)
        elif self.value() == "0":
            return annotated.filter(num_unarchived_repos__gt=0)
        else:
            return queryset


class NewRepositoryInline(admin.StackedInline):
    """Inline form for new Repository."""

    form = NewRepositoryInlineForm
    model = NewRepository
    extra = 0

    readonly_fields = ("github_repo_id",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(github_repo_id__isnull=True)

    # def get_extra(self, request, obj=None, **kwargs):
    # """Only show an extra inline if none exist."""
    # return 0 if obj else 1


class ExistingRepositoryInline(admin.StackedInline):
    form = ExistingRepositoryInlineForm
    model = ExistingRepository
    extra = 0

    template = "admin/existing_repository_inline.html"

    class Media:
        js = ("admin/js/fetch_repo.js",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(github_repo_id__isnull=False)


class MailinglistInline(admin.StackedInline):
    """Inline form for MailingList."""

    model = MailingList.projects.through
    extra = 1

    def get_extra(self, request, obj=None, **kwargs):
        """Only show an extra inline if none exist."""
        return 0 if obj else 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Custom admin for projects."""

    form = ProjectAdminForm
    list_filter = [
        ProjectAdminClientFilter,
        ProjectAdminSemesterFilter,
        ProjectAdminArchivedFilter,
    ]
    list_display = ["name", "client", "is_archived", "number_of_repos"]

    actions = [
        "create_mailing_lists",
        "synchronise_to_GitHub",
        "archive_all_repositories",
        "export_project_members",
    ]
    inlines = [
        NewRepositoryInline,
        ExistingRepositoryInline,
        MailinglistInline,
    ]

    search_fields = ("name",)
    readonly_fields = ("github_team_id",)
    dont_save_on_project_fields = (
        "description",
        "client",
        "comments",
        "github_team_id",
    )

    def save_model(self, request, obj, form, change):
        # This automatically appends the year of the semester to the slug when saving
        super().save_model(request, obj, form, change)

        obj.slug = slugify(f"{obj.name}-{obj.semester.year}")
        obj.save(update_fields=["slug"])

        if obj.default_repo:
            obj.repository_set.create(
                name=obj.slug,
            )
            obj.default_repo = False
            obj.save(update_fields=["default_repo"])

        queryset = Project.objects.filter(pk=obj.pk)
        if not change:  # new project
            self.synchronise_to_GitHub(request, queryset)
        else:  # existing
            for field in form.changed_data:  # field names
                if field not in self.dont_save_on_project_fields:
                    self.synchronise_to_GitHub(request, queryset)
                    break

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        project = form.instance

        should_sync = False
        for formset in formsets:
            # skip mailing lists
            if formset.model not in (NewRepository, ExistingRepository):
                continue

            if (
                formset.new_objects
                or formset.changed_objects  #  existing
                or formset.deleted_objects
            ):
                should_sync = True

        if should_sync:
            self.synchronise_to_GitHub(
                request, Project.objects.filter(pk=project.pk)
            )

    def delete_queryset(self, request, queryset):
        """Override delete action"""
        self.synchronise_to_GitHub(request, queryset)
        super().delete_queryset(request, queryset)

    def delete_model(self, request, obj):
        """This override triggers only from a specific project's change page."""
        self.synchronise_to_GitHub(request, Project.objects.filter(pk=obj.pk))

        super().delete_model(request, obj)

    def is_archived(self, instance):
        """Return the archived status of a Project instance (required to display property as check mark)."""
        return instance.is_archived != Repository.Archived.NOT_ARCHIVED

    # Instruct Django admin to display is_archived as check mark
    is_archived.boolean = True
    is_archived.short_description = "Project archived"

    def archive_all_repositories(self, request, queryset):
        """Archive all the repositories for the selected projects."""
        num_archived = 0
        for project in queryset:
            num_archived += Repository.objects.filter(
                is_archived=Repository.Archived.NOT_ARCHIVED, project=project
            ).update(is_archived=Repository.Archived.PENDING)
        messages.success(
            request,
            f"Succesfully archived {num_archived} repositories.",
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
        if not request.user.has_perm(
            f"{ProjectsConfig.label}.can_sync_to_github"
        ):
            raise PermissionDenied

        sync = GitHubSync(queryset)
        task = sync.perform_asynchronous_sync()
        return redirect("admin:progress_bar", task=task)

    synchronise_to_GitHub.short_description = (
        "Synchronise selected projects to GitHub"
    )

    def export_project_members(self, request, queryset):
        """Export project members to a CSV file."""
        content = StringIO()
        writer = csv.writer(
            content, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
        )
        writer.writerow(
            [
                "Project",
                "First name",
                "Last name",
                "Student number",
                "GitHub username",
                "Role",
            ]
        )

        for project in queryset:
            for registration in project.registration_set.all():
                user = registration.user
                writer.writerow(
                    [
                        project.name,
                        user.first_name,
                        user.last_name,
                        user.student_number,
                        user.github_username,
                        registration.course,
                    ]
                )

        response = HttpResponse(
            content.getvalue(), content_type="application/x-zip-compressed"
        )
        response["Content-Disposition"] = (
            "attachment; filename=project-members.csv"
        )
        return response

    export_project_members.short_description = "Export project members to CSV"

    def get_actions(self, request):
        """Override to hide certain actions from the UI"""
        actions = super().get_actions(request)

        if not request.user.has_perm(
            f"{ProjectsConfig.label}.can_sync_to_github"
        ):
            del actions["synchronise_to_GitHub"]

        return actions

    def synchronise_current_projects_to_GitHub(self, request):
        """Synchronise project(teams) of the current semester to GitHub."""
        if not request.user.has_perm(
            f"{ProjectsConfig.label}.can_sync_to_github"
        ):
            raise PermissionDenied

        return self.synchronise_to_GitHub(
            request,
            [
                p
                for p in Project.objects.filter(
                    semester=Semester.objects.get_or_create_current_semester()
                )
                if p.is_archived != Repository.Archived.CONFIRMED
            ],
        )

    def fetch_repo(self, request):
        repo_id = request.GET.get("github_repo_id")

        if not repo_id:
            return JsonResponse(
                {"error": "missing github_repo_id"}, status=400
            )

        if not repo_id.isdigit():
            return JsonResponse(
                {"error": "github_repo_id must be an integer"}, status=400
            )
        repo_id = int(repo_id)

        talker = GitHubAPITalker()
        try:
            repo: GithubRepository = talker.get_repo(repo_id)
        except UnknownObjectException:
            return JsonResponse(
                {"error": "repository with provided id does not exist"},
                status=404,
            )
        except GithubException as e:
            return JsonResponse({"error": e.message}, status=e.status)

        archived = Repository.Archived.NOT_ARCHIVED
        if repo.archived:
            archived = Repository.Archived.CONFIRMED

        return JsonResponse(
            {"name": repo.name, "private": repo.private, "archived": archived}
        )

    def get_urls(self):
        """Get admin urls."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync-to-github/",
                self.admin_site.admin_view(
                    self.synchronise_current_projects_to_GitHub
                ),
                name="synchronise_to_github",
            ),
            path(
                "fetch-repo/",
                self.admin_site.admin_view(self.fetch_repo),
                name="fetch_repo",
            ),
        ]
        return custom_urls + urls


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Custom admin for clients."""

    search_fields = ("name",)
