import csv
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
                writer = csv.writer(content, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
                writer.writerow(
                    ["Group Email [Required]", "Member Email", "Member Name", "Member Role", "Member Type"]
                )

                for user in User.objects.filter(registration__project=project):
                    writer.writerow([project.email, user.email, "Member", "MEMBER", "USER"])

                zip_file.writestr(project.email + ".csv", content.getvalue())

        response = HttpResponse(zip_content.getvalue(), content_type="application/x-zip-compressed")
        response["Content-Disposition"] = "attachment; filename=" + "project-addresses-export.zip"
        return response


admin.site.register(Client)
