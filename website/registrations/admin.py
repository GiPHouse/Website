from django.contrib import admin
from django.contrib.auth import get_user_model

from registrations.models import Employee, Registration

User: Employee = get_user_model()


class RegistrationInline(admin.StackedInline):
    """Inline form for Registration."""

    model = Registration
    extra = 0


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Custom admin for Student."""

    fields = ("first_name", "last_name", "email", "student_number", "github_id", "github_username", "date_joined")
    inlines = [RegistrationInline]
    list_display = ("full_name", "get_preference1", "get_preference2", "get_preference3")
    actions = ["place_in_first_project_preference"]

    list_filter = ("registration__semester", "registration__project", "registration__course")

    # Necessary for the autocomplete filter
    search_fields = ("first_name", "last_name")

    def full_name(self, obj):
        """Return full name of student."""
        return f"{obj.first_name} {obj.last_name}"

    def get_preference1(self, obj):
        """Return 1st project preference of Student."""
        registration = obj.registration_set.first()
        return registration.preference1 if registration else None

    get_preference1.short_description = "Preference1"
    get_preference1.admin_order_field = "github_username"

    def get_preference2(self, obj):
        """Return 2nd project preference of Student."""
        registration = obj.registration_set.first()
        return registration.preference2 if registration else None

    get_preference2.short_description = "Preference2"
    get_preference2.admin_order_field = "github_username"

    def get_preference3(self, obj):
        """Return 3rd project preference of Student."""
        registration = obj.registration_set.first()
        return registration.preference3 if registration else None

    get_preference3.short_description = "Preference3"
    get_preference3.admin_order_field = "github_username"

    def place_in_first_project_preference(self, request, queryset):
        """Place the selected users in their first project preference."""
        for user in queryset:
            registration = user.registration_set.first()
            registration.project = registration.preference1
            registration.save()
