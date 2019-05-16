from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User as DjangoUser

from projects.models import Project

from registrations.models import GiphouseProfile, Registration, Role, RoleEnum

User: DjangoUser = get_user_model()
admin.site.unregister(User)
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


class StudentForm(forms.ModelForm):
    """Admin form to edit Students."""

    class Meta:
        """Meta class for StudentForm."""

        model = User
        fields = ('first_name', 'last_name', 'email', 'date_joined')
        exclude = []

    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
    )

    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        """Dynamically setup form."""
        super().__init__(*args, **kwargs)

        self.fields['role'].initial = Role.objects.filter(user=self.instance).first()

        self.fields['project'].initial = Project.objects.filter(user=self.instance).first()

    def save_m2m(self):
        """Add the Role to the user."""
        groups = []
        role = self.cleaned_data['role']
        project = self.cleaned_data['project']
        if role:
            groups.append(role)
        if project:
            groups.append(project)
        self.instance.groups.set(groups)

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super().save()
        self.save_m2m()
        return instance


@admin.register(User)
class StudentAdmin(admin.ModelAdmin):
    """Custom admin for Student."""

    form = StudentForm
    inlines = [GiphouseProfileInline, RegistrationInline]
    list_display = ('first_name', 'last_name', 'get_github_username', 'get_role')
    actions = ['place_in_first_project_preference']

    # Necessary for the autocomplete filter
    search_fields = ('first_name', 'last_name')

    def get_queryset(self, request):
        """Return queryset of all GiPHouse users."""
        return self.model.objects.filter(giphouseprofile__isnull=False)

    def get_github_username(self, obj):
        """Return github_username of Student."""
        return obj.giphouseprofile.github_username
    get_github_username.short_description = 'Github Username'
    get_github_username.admin_order_field = 'giphouseprofile__github_username'

    def get_role(self, obj):
        """Return role of Student."""
        try:
            return (set(obj.groups.values_list('name', flat=True)) & set([r.value for r in RoleEnum])).pop()
        except KeyError:
            return None
    get_role.short_description = 'Role'

    def place_in_first_project_preference(self, request, queryset):
        """Place the selected users in their first project preference."""
        for user in queryset:
            registration = user.registration_set.order_by('semester').first()
            user.groups.add(registration.preference1)
            user.save()


admin.site.register(Role)
