from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User as DjangoUser

from courses.models import Semester

from projects.models import Project

from registrations.forms import StudentAdminForm
from registrations.models import GiphouseProfile, Registration, Role, Student

User: DjangoUser = get_user_model()
admin.site.unregister(Group)


class StudentAdminProjectFilter(admin.SimpleListFilter):
    """Filter class to filter current Project objects."""

    title = "Current Projects"
    parameter_name = "project"

    def lookups(self, request, model_admin):
        """List the current projects."""
        return (
            (project.id, project.name)
            for project in Project.objects.filter(semester=Semester.objects.get_current_semester())
        )

    def queryset(self, request, queryset):
        """Filter out participants in the specified Project."""
        if self.value():
            return queryset.filter(groups__id=self.value())
        return queryset


class StudentAdminSemesterFilter(admin.SimpleListFilter):
    """Filter class to filter current Semester objects."""

    title = "Semester"
    parameter_name = "semester"

    def lookups(self, request, model_admin):
        """List the current projects."""
        return ((semester.id, str(semester)) for semester in Semester.objects.all())

    def queryset(self, request, queryset):
        """Filter out participants in the specified Project."""
        if self.value():
            project_ids = Project.objects.filter(semester__id=self.value())
            return queryset.filter(groups__id__in=project_ids)
        return queryset


class StudentAdminRoleFilter(admin.SimpleListFilter):
    """Filter class to filter current Project objects."""

    title = "Roles"
    parameter_name = "role"

    def lookups(self, request, model_admin):
        """List the current projects."""
        return ((role.id, role.name) for role in Role.objects.all())

    def queryset(self, request, queryset):
        """Filter out participants in the specified Project."""
        if self.value():
            return queryset.filter(groups__id=self.value())
        return queryset


class GiphouseProfileInline(admin.StackedInline):
    """Inline form for GiphouseProfile."""

    model = GiphouseProfile
    max_num = 1
    min_num = 0


class RegistrationInline(admin.StackedInline):
    """Inline form for Registration."""

    model = Registration
    max_num = 1
    min_num = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Custom admin for Student."""

    form = StudentAdminForm
    inlines = [GiphouseProfileInline, RegistrationInline]
    list_display = ("full_name", "get_role", "get_preference1", "get_preference2", "get_preference3")
    actions = ["place_in_first_project_preference"]

    list_filter = (StudentAdminProjectFilter, StudentAdminSemesterFilter, StudentAdminRoleFilter)

    # Necessary for the autocomplete filter
    search_fields = ("first_name", "last_name")

    def full_name(self, obj):
        """Return full name of student."""
        return f"{obj.first_name} {obj.last_name}"

    def get_queryset(self, request):
        """Return queryset of all GiPHouse users."""
        return self.model.objects.filter(giphouseprofile__isnull=False)

    def get_preference1(self, obj):
        """Return 1st project preference of Student."""
        registration = obj.registration_set.order_by("semester").first()
        return registration.preference1 if registration else None

    get_preference1.short_description = "Preference1"
    get_preference1.admin_order_field = "giphouseprofile__github_username"

    def get_preference2(self, obj):
        """Return 2nd project preference of Student."""
        registration = obj.registration_set.order_by("semester").first()
        return registration.preference2 if registration else None

    get_preference2.short_description = "Preference2"
    get_preference2.admin_order_field = "giphouseprofile__github_username"

    def get_preference3(self, obj):
        """Return 3rd project preference of Student."""
        registration = obj.registration_set.order_by("semester").first()
        return registration.preference3 if registration else None

    get_preference3.short_description = "Preference3"
    get_preference3.admin_order_field = "giphouseprofile__github_username"

    def get_role(self, obj):
        """Return role of Student."""
        return Role.objects.get(user=obj)

    get_role.short_description = "Role"

    def place_in_first_project_preference(self, request, queryset):
        """Place the selected users in their first project preference."""
        for user in queryset:
            registration = user.registration_set.order_by("semester").first()
            user.groups.add(registration.preference1)
            user.save()


admin.site.register(Role)
