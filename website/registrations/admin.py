from django.contrib import admin
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User as DjangoUser
from django.template.loader import get_template

from registrations.forms import StudentAdminForm
from registrations.models import GiphouseProfile, Registration, Role, Student
from projects.models import Project

from django.shortcuts import render


User: DjangoUser = get_user_model()
admin.site.unregister(Group)


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
    list_display = ('full_name', 'get_role', 'get_preference1',
                    'get_preference2', 'get_preference3', 'current_project')
    actions = ['place_in_first_project_preference']

    # Necessary for the autocomplete filter
    search_fields = ('first_name', 'last_name')

    def full_name(self, obj):
        """Return full name of student."""
        return f'{obj.first_name} {obj.last_name}'

    def get_queryset(self, request):
        """Return queryset of all GiPHouse users."""
        return self.model.objects.filter(giphouseprofile__isnull=False)

    def get_preference1(self, obj):
        """Return github_username of Student."""
        registration = obj.registration_set.order_by('semester').first()
        return registration.preference1 if registration else None
    get_preference1.short_description = 'Preference1'
    get_preference1.admin_order_field = 'giphouseprofile__github_username'

    def get_preference2(self, obj):
        """Return github_username of Student."""
        registration = obj.registration_set.order_by('semester').first()
        return registration.preference2 if registration else None
    get_preference2.short_description = 'Preference2'
    get_preference2.admin_order_field = 'giphouseprofile__github_username'

    def get_preference3(self, obj):
        """Return github_username of Student."""
        registration = obj.registration_set.order_by('semester').first()
        return registration.preference3 if registration else None
    get_preference3.short_description = 'Preference3'
    get_preference3.admin_order_field = 'giphouseprofile__github_username'

    def get_role(self, obj):
        """Return role of Student."""
        return Role.objects.get(user=obj)
    get_role.short_description = 'Role'

    def current_project(self, obj):
        if not obj.registration_set.order_by('semester').first():
            return None

        field = forms.ModelChoiceField(
            queryset=Project.objects.filter(semester=obj.registration_set.order_by('semester').first().semester),
            required=False,
        )
        template = get_template('registrations/project_widget.html')
        context = {
            'field': field.widget.render("project", ""),
            'obj': obj
        }
        return template.render(context)
    current_project.short_description = 'Current Project'
    current_project.allow_tags = True

    def place_in_first_project_preference(self, request, queryset):
        """Place the selected users in their first project preference."""
        for user in queryset:
            registration = user.registration_set.order_by('semester').first()
            user.groups.add(registration.preference1)
            user.save()


admin.site.register(Role)
