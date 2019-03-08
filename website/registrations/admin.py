from django import forms
from django.contrib import admin

from django.contrib.auth import get_user_model

from registrations.models import GiphouseProfile, Registration

User = get_user_model()


class GiphouseProfileForm(forms.ModelForm):
    """GiphouseProfile form for admin."""

    github_username = forms.CharField(widget=forms.TextInput)


class GiphouseProfileInline(admin.StackedInline):
    """Inline form for GiphouseProfile."""

    model = GiphouseProfile
    form = GiphouseProfileForm
    max_num = 1
    min_num = 0


class RegistrationInline(admin.StackedInline):
    """Inline form for Registration."""

    model = Registration
    max_num = 1
    min_num = 0


class Student(User):
    """Proxy model for user."""

    class Meta:
        """Meta class Specifying that this model is a proxy model."""

        proxy = True

    def __str__(self):
        """Return first and last name."""
        return f'{self.first_name} {self.last_name}'

    @property
    def github_username(self):
        """Return github_username of Student."""
        return self.giphouseprofile.github_username


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Custom admin for Student."""

    inlines = [GiphouseProfileInline, RegistrationInline]
    list_display = ('first_name', 'last_name', 'github_username')
    fields = ('first_name', 'last_name', 'email', 'date_joined', 'groups')

    def get_queryset(self, request):
        """Return queryset of all GiPHouse users."""
        return self.model.objects.filter(giphouseprofile__isnull=False)
