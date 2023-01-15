import csv
from io import StringIO

from admin_auto_filters.filters import AutocompleteFilter

from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.views import View

from courses.models import Semester

from projects.models import Project

from registrations.models import Employee, Registration
from registrations.team_assignment import CSV_STRUCTURE, TeamAssignmentGenerator

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

    actions = (
        "place_in_first_project_preference",
        "unassign_from_project",
        "export_student_numbers",
        "export_registrations",
        "generate_project_assignment_proposal",
    )

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
        "get_current_project",
        "is_staff",
    )

    list_filter = (
        UserAdminSemesterFilter,
        UserAdminProjectFilter,
        "registration__course",
        "registration__experience",
        "is_staff",
        "registration__is_international",
        "registration__available_during_scheduled_timeslot_1",
        "registration__available_during_scheduled_timeslot_2",
        "registration__available_during_scheduled_timeslot_3",
        "registration__has_problems_with_signing_an_nda",
    )

    # Necessary for the autocomplete filter
    search_fields = ("first_name", "last_name", "student_number", "github_username")

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

    def export_student_numbers(self, request, queryset):
        """Export the first name, last name and student number of the selected users to a CSV file."""
        content = StringIO()
        writer = csv.writer(content, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["First name", "Last name", "Student number"])
        for user in queryset:
            writer.writerow([user.first_name, user.last_name, user.student_number])

        response = HttpResponse(content.getvalue(), content_type="application/x-zip-compressed")
        response["Content-Disposition"] = "attachment; filename=student-numbers.csv"
        return response

    export_student_numbers.short_description = "Export names and student numbers"

    def export_registrations(self, request, queryset):
        """Export the registration information of the most recent registration of the selected users to a CSV file."""
        content = StringIO()
        writer = csv.writer(content, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(
            [
                "First name",
                "Last name",
                "Student number",
                "GitHub username",
                "Course",
                "1st project preference",
                "2nd project preference",
                "3rd project preference",
                "1st partner preference",
                "2nd partner preference",
                "3rd partner preference",
                "Experience",
                "Non-dutch",
                "Available during scheduled timeslot 1",
                "Available during scheduled timeslot 2",
                "Available during scheduled timeslot 3",
                "Has problems with signing an NDA",
                "Registration Comments",
            ]
        )
        for user in queryset:
            registration = user.registration_set.first()
            writer.writerow(
                [
                    user.first_name,
                    user.last_name,
                    user.student_number,
                    user.github_username,
                    registration.course,
                    registration.preference1,
                    registration.preference2,
                    registration.preference3,
                    registration.partner_preference1,
                    registration.partner_preference2,
                    registration.partner_preference3,
                    registration.experience,
                    registration.is_international,
                    registration.available_during_scheduled_timeslot_1,
                    registration.available_during_scheduled_timeslot_2,
                    registration.available_during_scheduled_timeslot_3,
                    registration.has_problems_with_signing_an_nda,
                    registration.comments,
                ]
            )

        response = HttpResponse(content.getvalue(), content_type="application/x-zip-compressed")
        response["Content-Disposition"] = "attachment; filename=registrations.csv"
        return response

    def unassign_from_project(self, request, queryset):
        """Clear the set project for a registration."""
        num_unassigned = 0
        for user in queryset:
            reg = user.registration_set.first()
            if reg is not None and reg.project is not None:
                reg.project = None
                reg.save()
                num_unassigned += 1
        messages.success(
            request,
            f"Succesfully unassigned {num_unassigned} registrations.",
        )

    def generate_project_assignment_proposal(self, request, queryset):
        """Create task to compute project assignment."""
        registrations = [user.registration_set.first() for user in queryset]

        if None in registrations:
            messages.warning(request, "All users should have a registration.")
            return

        if len(set(registration.semester for registration in registrations)) > 1:
            messages.warning(request, "All users should have a registration in the same semester.")
            return

        task = TeamAssignmentGenerator(registrations).start_solve_task()
        return redirect("admin:progress_bar", task=task.id)

    def get_urls(self):
        """Get admin urls."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(ImportAssignmentAdminView.as_view()),
                name="import",
            ),
        ]
        return custom_urls + urls


class CsvImportForm(forms.Form):
    """Form used when importing a csv group assignment."""

    csv_file = forms.FileField(required=True)
    semester = forms.ModelChoiceField(queryset=Semester.objects.all(), required=True)


class ImportAssignmentAdminView(View):
    """Import a CSV file with project assignment."""

    def get(self, request):
        """Get a form to select the semester to import for."""
        form = CsvImportForm()
        payload = {"form": form, "header": CSV_STRUCTURE[:5], "title": "Import"}

        return render(request, "admin/registrations/import-csv.html", payload)

    @staticmethod
    def handle_csv(csv_file, semester):
        """Process a CSV file with project assignment."""
        csv_data = csv_file.read().decode("utf-8")
        dialect = csv.Sniffer().sniff(csv_data)
        reader = csv.reader(StringIO(csv_data), dialect=dialect)

        num_assigned = 0
        num_ignored = 0

        expected_header = CSV_STRUCTURE[:5]

        for row in reader:
            if reader.line_num == 1 and row[:5] != expected_header:
                raise ValueError("Invalid columns")
            elif reader.line_num == 1 or not row[4]:
                continue

            csv_first_name = row[0]
            csv_last_name = row[1]
            csv_student_number = row[2]
            csv_course = row[3]
            csv_project = row[4]

            try:
                project = Project.objects.get(name=csv_project, semester=semester)
            except Project.DoesNotExist:
                raise ValueError(f"No project was found for {csv_project} in semester {semester}.")

            try:
                registration = Registration.objects.get(
                    user__first_name=csv_first_name,
                    user__last_name=csv_last_name,
                    semester=semester,
                    course__name=csv_course,
                    user__student_number=csv_student_number,
                )
            except Registration.DoesNotExist:
                raise ValueError(
                    f"No registration was found for {csv_first_name} {csv_last_name} with student number "
                    f"{csv_student_number} in semester {semester} for course {csv_course}. "
                )

            if registration.project:
                num_ignored += 1
            else:
                registration.project = project
                registration.save()
                num_assigned += 1

        return num_assigned, num_ignored

    def post(self, request):
        """Import and process a .csv file with assigned projects."""
        csv_file = request.FILES["csv_file"]
        semester = Semester.objects.get(pk=request.POST.get("semester"))
        if not csv_file.name.endswith(".csv"):
            messages.error(request, "File is not CSV type")
        elif csv_file.multiple_chunks():
            messages.error(request, "Uploaded file is too big (%.2f MB)." % (csv_file.size / (1000 * 1000),))
        else:
            try:
                num_assigned, num_ignored = self.handle_csv(csv_file, semester)
                messages.success(
                    request,
                    f"CSV file has been imported. {num_assigned} registrations are updated. "
                    f"{num_ignored} registrations were already assigned and not been overwritten.",
                )
            except ValueError as e:
                messages.error(request, e)
        return redirect("..")


class DownloadAssignmentForm(forms.Form):
    """Form used when generating and downloading a team assignment."""

    semester = forms.ModelChoiceField(queryset=Semester.objects.all(), required=True)
