from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin
from django.contrib.auth import get_user_model

from registrations.models import Employee, Registration

User: Employee = get_user_model()


class UserAdminSemesterFilter(AutocompleteFilter):
    """Filter class to filter Semester objects."""

    title = "Semester"
    field_name = "semester"
    rel_model = Registration

    def queryset(self, request, queryset):
        """Filter semesters."""
        if self.value():
            return queryset.filter(registration__semester=self.value())
        else:
            return queryset


class UserAdminProjectFilter(AutocompleteFilter):
    """Filter class to filter current Project objects."""

    title = "Projects"
    field_name = "project"
    rel_model = Registration

    def queryset(self, request, queryset):
        """Filter out participants in the specified Project."""
        if self.value():
            return queryset.filter(registration__project=self.value())
        return queryset


class RegistrationInline(admin.StackedInline):
    """Inline form for Registration."""

    model = Registration
    extra = 0


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Custom admin for Student."""

    actions = ["place_in_first_project_preference"]

    fieldsets = (
        ("Personal", {"fields": ("first_name", "last_name", "email", "student_number")}),
        (
            "Administration",
            {
                "fields": ("date_joined", "is_staff", "is_active", "is_superuser", "user_permissions"),
                "classes": ("collapse",),
            },
        ),
        ("GitHub", {"fields": ("github_id", "github_username"), "classes": ("collapse",)}),
        ("Private comments", {"fields": ("comments",)}),
    )

    inlines = [RegistrationInline]
    list_display = (
        "__str__",
        "github_username",
        "get_current_project",
        "get_experience",
        "get_preference1",
        "get_preference2",
        "get_preference3",
        "is_staff",
    )

    list_filter = (
        UserAdminSemesterFilter,
        UserAdminProjectFilter,
        "registration__course",
        "registration__experience",
        "is_staff",
    )

    # Necessary for the autocomplete filter
    search_fields = ("first_name", "last_name", "student_number", "github_username")

    def get_preference1(self, obj):
        """Return 1st project preference."""
        registration = obj.registration_set.first()
        return registration.preference1 if registration else None

    get_preference1.short_description = "First Preference"

    def get_preference2(self, obj):
        """Return 2nd project preference."""
        registration = obj.registration_set.first()
        return registration.preference2 if registration else None

    get_preference2.short_description = "Preference2"

    def get_preference3(self, obj):
        """Return 3rd project preference."""
        registration = obj.registration_set.first()
        return registration.preference3 if registration else None

    get_preference3.short_description = "Preference3"

    def get_experience(self, obj):
        """Return experience."""
        registration = obj.registration_set.first()
        return registration.get_experience_display() if registration else None

    get_experience.short_description = "Experience"

    def get_current_project(self, obj):
        """Return current project."""
        registration = obj.registration_set.first()
        return registration.project if registration else None

    get_current_project.short_description = "Project"

    def place_in_first_project_preference(self, request, queryset):
        """Place the selected users in their first project preference."""
        for user in queryset:
            registration = user.registration_set.first()
            registration.project = registration.preference1
            registration.save()

    class Media:
        """Necessary to use AutocompleteFilter."""
