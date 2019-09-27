import zipfile
from io import BytesIO, StringIO

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from projects.forms import ProjectAdminForm
from projects.models import Client, Project

from registrations.models import Employee

User: Employee = get_user_model()


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Custom admin for projects."""

    form = ProjectAdminForm
    list_filter = ["semester"]
    exclude = ["permissions"]
    actions = ["export_addresses_csv"]

    def export_addresses_csv(self, request, queryset):
        """Export the selected projects as email CSV zip."""
        zip_content = BytesIO()
        with zipfile.ZipFile(zip_content, "w") as zip_file:

            for project in queryset:
                content = StringIO()
                project_email = project.email
                print(
                    '"Group Email [Required]","Member Email","Member Name","Member Role","Member Type"', file=content
                )
                print(f'"{project_email}","watchers@giphouse.nl","Archive GiPHouse","MEMBER","USER"', file=content)
                for user in User.objects.filter(registration__project=project):
                    print(f'"{project_email}","{user.email}","Member","MEMBER","USER"', file=content)

                zip_file.writestr(project_email + ".csv", content.getvalue())

        response = HttpResponse(zip_content.getvalue(), content_type="application/x-zip-compressed")
        response["Content-Disposition"] = "attachment; filename=" + "project-addresses-export.zip"
        return response


admin.site.register(Client)
