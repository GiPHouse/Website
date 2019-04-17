from django.contrib import admin
from django.contrib.auth.models import User as DjangoUser, Group
from django.contrib.auth import get_user_model

from registrations.models import GiphouseProfile, Registration

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


@admin.register(User)
class StudentAdmin(admin.ModelAdmin):
    """Custom admin for Student."""

    inlines = [GiphouseProfileInline, RegistrationInline]
    list_display = ('first_name', 'last_name', 'get_github_username', 'get_role')
    fields = ('first_name', 'last_name', 'email', 'date_joined', 'groups')

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
        return obj.giphouseprofile.get_role_display()
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'giphouseprofile__role'
