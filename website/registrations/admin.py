import csv
from io import StringIO

from admin_auto_filters.filters import AutocompleteFilter

from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.views import View
from django.utils.safestring import mark_safe
from django.forms.models import BaseInlineFormSet
# from django.core.exceptions import ValidationError

from courses.models import Semester, Course

from registrations.utils.sample_registration_form import SampleRegistrationForm

from projects.models import Project

from nested_admin import NestedModelAdmin, NestedTabularInline

from registrations.models import Employee
from registrations.models.registration import (
    Question,
    QuestionChoice,
    Registrations,
    RegistrationSubmission,
    Answer,
)
from registrations.team_assignment import (
    CSV_STRUCTURE,
)

User: Employee = get_user_model()

SAMPLE_MIN_CHOICES = 0
SAMPLE_MAX_CHOICES = 3

"The following four classes provide the logic behind the admin"
"interface for Registrationss with the proper inlines."


class QuestionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        # required_labels = {
        #     label
        #     for (label, _, must_be_set) in Question.QUESTION_LABELS
        #     if must_be_set
        # }

        used_labels = set()

        for form in self.forms:
            if form.cleaned_data.get("DELETE"):
                continue
            if not form.cleaned_data:
                continue

            label = form.cleaned_data.get("label")
            if label:
                used_labels.add(label)

        # missing = required_labels - used_labels
        # if missing:
        #     raise ValidationError(
        #         f"Missing required labels: {', '.join(missing)}"
        #     )


class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get("question_type")
        min_choices = cleaned_data.get("min_choices")
        max_choices = cleaned_data.get("max_choices")

        errors = []

        if question_type == Question.MULTI:
            if min_choices is not None and min_choices < 0:
                errors.append("min_choices cannot be negative.")
            if max_choices is not None and max_choices < 0:
                errors.append("max_choices cannot be negative.")
            if (
                min_choices is not None
                and max_choices is not None
                and min_choices > max_choices
            ):
                errors.append(
                    "min_choices cannot be greater than max_choices."
                )

            if self.instance and self.instance.pk:
                choice_count = self.instance.choices.count()
                if min_choices is not None and min_choices > choice_count:
                    errors.append(
                        f"min_choices ({min_choices}) cannot exceed the number of choices ({choice_count})."
                    )
                if max_choices is not None and max_choices > choice_count:
                    errors.append(
                        f"max_choices ({max_choices}) cannot exceed the number of choices ({choice_count})."
                    )

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data


class FollowUpQuestionChoiceInline(NestedTabularInline):
    model = QuestionChoice
    extra = 0
    fk_name = "question"
    inlines = []


class FollowUpQuestionInline(NestedTabularInline):
    model = Question
    fk_name = "parent_choice"
    extra = 0
    exclude = ["parent_choice", "registration"]
    inlines = [FollowUpQuestionChoiceInline]


class QuestionChoiceInline(NestedTabularInline):
    model = QuestionChoice
    extra = 0
    fk_name = "question"
    inlines = [FollowUpQuestionInline]


class QuestionInline(NestedTabularInline):
    model = Question
    fk_name = "registration"
    form = QuestionAdminForm
    formset = QuestionInlineFormSet
    extra = 0
    exclude = ["parent_choice"]
    inlines = [QuestionChoiceInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(parent_choice__isnull=True)

    class Media:
        js = ("js/question_type_toggle_admin.js",)


@admin.register(Registrations)
class RegistrationsAdmin(NestedModelAdmin):
    list_display = ("title", "semester")
    inlines = [QuestionInline]

    # Override get_urls to add custom url for sample registration
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "create-sample/",
                self.admin_site.admin_view(self.create_sample_registration),
                name="create-sample-registration",
            )
        ]
        return custom_urls + urls

    # Create a sample registration with autofilled questions
    def create_sample_registration(self, request):
        sample_registration = SampleRegistrationForm()
        sample_questions = sample_registration.get_sample_questions()
        reg = sample_registration.reg

        for item in sample_questions:
            label, text, qtype, choices = item

            q = Question.objects.create(
                registration=reg,
                label=label,
                question=text,
                question_type=qtype,
            )

            if qtype in [Question.TEXTLIST, Question.CHOICELIST]:
                q.min_choices = SAMPLE_MIN_CHOICES
                q.max_choices = SAMPLE_MAX_CHOICES
                q.save()

            for choice_text in choices:
                QuestionChoice.objects.create(question=q, value=choice_text)

        url = reverse(
            "admin:registrations_registrations_change", args=[reg.pk]
        )
        return redirect(url)

    # Set changelist to add button that calls create_sample_registration
    change_list_template = "admin/registrations/change_list.html"


@admin.register(Question)
class QuestionAdmin(NestedModelAdmin):
    form = QuestionAdminForm
    list_display = (
        "question",
        "registration",
        "question_type",
        "label",
        "optional",
    )
    inlines = [QuestionChoiceInline]


class AnswerInline(NestedTabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question_text", "answer_value")
    exclude = ("question",)

    def question_text(self, obj):
        return obj.question.question

    question_text.short_description = "Question"

    def answer_value(self, obj):
        return obj.answer_value

    answer_value.short_description = "Answer"


@admin.register(RegistrationSubmission)
class RegistrationSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "registration",
        "participant",
        "participant_github_id",
        "participant_github_username",
        "submitted",
        "created",
    )
    readonly_fields = ("participant_github_id", "participant_github_username")
    inlines = [AnswerInline]

    def participant_github_id(self, obj):
        return obj.participant.github_id

    participant_github_id.short_description = "GitHub ID"

    def participant_github_username(self, obj):
        return obj.participant.github_username

    participant_github_username.short_description = "GitHub Username"


class AnswerInline(NestedTabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question_text", "answer_value")
    exclude = ("question",)

    def question_text(self, obj):
        return obj.question.question

    question_text.short_description = "Question"

    def answer_value(self, obj):
        return obj.answer_value

    answer_value.short_description = "Answer"


class UserAdminSemesterFilter(admin.SimpleListFilter):
    """Filter class to filter Semester objects."""

    title = "Semester"
    parameter_name = "semester"
    rel_model = Registrations

    def lookups(self, request, model_admin):
        """Defines all the filter options including All"""
        semesters = Semester.objects.all()
        id = 1
        filter_options = [(0, "All ")]
        for s in semesters:
            filter_options.append((id, s))
            id += 1
        return filter_options

    def choices(self, changelist):
        """Hides the non functional All button"""
        for choice in super().choices(changelist):
            if choice["display"] == "All":
                continue
            yield choice

    def value(self):
        """Autoselects the newest semester"""
        val = super().value()
        if val is not None:
            return val
        return str(1) if Semester.objects.all().first() else None

    def queryset(self, request, queryset):
        """Filter semesters."""
        if self.value() == "0":
            return queryset
        else:
            return queryset.filter(
                registrationsubmission__registration__semester=self.value()
            )


class UserAdminProjectFilter(AutocompleteFilter):
    """Filter class to filter current Project objects."""

    title = "Projects"
    field_name = "projects"
    rel_model = Registrations

    def lookups(self, request, model_admin):
        return [(c.id, c.name) for c in Course.objects.all()]

    def queryset(self, request, queryset):
        """Filter out participants in the specified Project."""
        if self.value():
            return queryset.filter(
                registrationsubmission__projects=self.value()
            )
        return queryset


class UserAdminCourseFilter(admin.SimpleListFilter):
    title = "Course"
    parameter_name = "course"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [(c.id, c.name) for c in Course.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                registrationsubmission__course__id=self.value()
            )
        return queryset


class UserAdminAnswerFilter(admin.SimpleListFilter):
    """Base class for filtering by answer value."""

    label = None

    def lookups(self, request, model_admin):
        raise NotImplementedError

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                registrationsubmission__answer__question__label=self.label,
                registrationsubmission__answer__choicedata__choice__value=self.value(),
            ).distinct()
        return queryset


class UserAdminDevExpFilter(UserAdminAnswerFilter):
    title = "Dev Experience"
    parameter_name = "devexp"
    label = "devexp"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [
            ("Beginner", "Beginner"),
            ("Intermediate", "Intermediate"),
            ("Advanced", "Advanced"),
        ]


class UserAdminGitExpFilter(UserAdminAnswerFilter):
    title = "Git Experience"
    parameter_name = "gitexp"
    label = "gitexp"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [
            ("Beginner", "Beginner"),
            ("Intermediate", "Intermediate"),
            ("Advanced", "Advanced"),
        ]


class UserAdminScrumExpFilter(UserAdminAnswerFilter):
    title = "Scrum Experience"
    parameter_name = "scrumexp"
    label = "scrumexp"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [
            ("Beginner", "Beginner"),
            ("Intermediate", "Intermediate"),
            ("Advanced", "Advanced"),
        ]


class UserAdminManagementFilter(UserAdminAnswerFilter):
    title = "Management Interest"
    parameter_name = "management"
    label = "management"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminInternationalFilter(UserAdminAnswerFilter):
    title = "Non-dutch"
    parameter_name = "nondutch"
    label = "nondutch"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot1Filter(UserAdminAnswerFilter):
    title = "Timeslot 1"
    parameter_name = "timeslot1"
    label = "timeslot1"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot2Filter(UserAdminAnswerFilter):
    title = "Timeslot 2"
    parameter_name = "timeslot2"
    label = "timeslot2"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot3Filter(UserAdminAnswerFilter):
    title = "Timeslot 3"
    parameter_name = "timeslot3"
    label = "timeslot3"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot4Filter(UserAdminAnswerFilter):
    title = "Timeslot 4"
    parameter_name = "timeslot4"
    label = "timeslot4"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot5Filter(UserAdminAnswerFilter):
    title = "Timeslot 5"
    parameter_name = "timeslot5"
    label = "timeslot5"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot6Filter(UserAdminAnswerFilter):
    title = "Timeslot 6"
    parameter_name = "timeslot6"
    label = "timeslot6"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot7Filter(UserAdminAnswerFilter):
    title = "Timeslot 7"
    parameter_name = "timeslot7"
    label = "timeslot7"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot8Filter(UserAdminAnswerFilter):
    title = "Timeslot 8"
    parameter_name = "timeslot8"
    label = "timeslot8"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot9Filter(UserAdminAnswerFilter):
    title = "Timeslot 9"
    parameter_name = "timeslot9"
    label = "timeslot9"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminTimeslot10Filter(UserAdminAnswerFilter):
    title = "Timeslot 10"
    parameter_name = "timeslot10"
    label = "timeslot10"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class UserAdminNdaFilter(UserAdminAnswerFilter):
    title = "Has problems with NDA"
    parameter_name = "nonda"
    label = "nonda"
    template = "admin/registrations/collapsible_filter.html"

    def lookups(self, request, model_admin):
        return [("True", "True"), ("False", "False")]


class RegistrationInline(NestedTabularInline):
    """Inline form for Registration."""

    model = Registrations
    extra = 0


class RegistrationSubmissionInline(NestedTabularInline):
    """Inline form for Registration."""

    model = RegistrationSubmission
    extra = 0
    inlines = [AnswerInline]

class CollapsedBooleanFieldFilter(admin.BooleanFieldListFilter):
    """Class to collapse boolean field filters on default"""

    template = "admin/registrations/collapsible_filter.html"


@admin.register(User)
class UserAdmin(NestedModelAdmin):
    """Custom admin for Student."""

    actions = (
        "unassign_from_project",
        "export_student_numbers",
        "export_registrations",
    )

    fieldsets = (
        (
            "Personal",
            {"fields": ("first_name", "last_name", "email", "student_number")},
        ),
        (
            "Administration",
            {
                "fields": (
                    "date_joined",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "GitHub",
            {
                "fields": ("github_id", "github_username"),
                "classes": ("collapse",),
            },
        ),
        ("Private comments", {"fields": ("comments",)}),
    )

    inlines = [RegistrationSubmissionInline]
    list_display = (
        "__str__",
        "get_current_project",
        "is_staff",
    )

    list_filter = (
        UserAdminSemesterFilter,
        UserAdminProjectFilter,
        UserAdminCourseFilter,
        UserAdminDevExpFilter,
        UserAdminGitExpFilter,
        UserAdminScrumExpFilter,
        UserAdminManagementFilter,
        UserAdminInternationalFilter,
        UserAdminTimeslot1Filter,
        UserAdminTimeslot2Filter,
        UserAdminTimeslot3Filter,
        UserAdminNdaFilter,
        ("is_staff", CollapsedBooleanFieldFilter),
    )

    # Necessary for the autocomplete filter
    search_fields = (
        "first_name",
        "last_name",
        "student_number",
        "github_username",
    )

    def get_current_project(self, obj):
        """Return current project."""
        submission = obj.registrationsubmission_set.last()

        if not submission:
            return None

        return mark_safe(
            "<br>".join(str(p) for p in submission.get_projects())
        )

    get_current_project.short_description = "Project"

    def export_student_numbers(self, request, queryset):
        """Export the first name, last name and student number of the selected users to a CSV file."""
        content = StringIO()
        writer = csv.writer(
            content, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
        )
        writer.writerow(["First name", "Last name", "Student number"])
        for user in queryset:
            writer.writerow(
                [user.first_name, user.last_name, user.student_number]
            )

        response = HttpResponse(
            content.getvalue(), content_type="application/x-zip-compressed"
        )
        response["Content-Disposition"] = (
            "attachment; filename=student-numbers.csv"
        )
        return response

    export_student_numbers.short_description = (
        "Export names and student numbers"
    )

    def convert_timeslots(self, timeslot_answers):
        # converts timeslot availability answers to a list of 10 true false values indicating availability for timeslots 1-10
        # Input: string like "available during scheduled timeslot 1, available during scheduled timeslot 2"
        # Output: [True, True, False, False, False, False, False, False, False, False]

        current_reg = Registrations.objects.current_registration()

        timeslot_db = list(
            QuestionChoice.objects.filter(
                question__label="timeslots",
                question__registration=current_reg,
            ).values_list("value", flat=True)
        )
        n = len(timeslot_db)
        timeslot_list = [False] * n

        if not timeslot_answers:
            return timeslot_list

        # Split by comma to get individual timeslot entries
        timeslot_entries = timeslot_answers.split(",")

        # Check if each entry matches a timeslot choice in the database, set corresponding index to True if it does
        for entry in timeslot_entries:
            entry = entry.strip()
            if entry in timeslot_db:
                index = timeslot_db.index(entry)
                timeslot_list[index] = True

        return timeslot_list

    def export_registrations(self, request, queryset):
        """Export the registration information of the most recent registration of the selected users to a CSV file."""
        content = StringIO()
        writer = csv.writer(
            content, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
        )
        queryset = queryset.exclude(registrationsubmission__isnull=True)

        # Static headers
        static_headers = [
            "First name",
            "Last name",
            "Student number",
            "GitHub username",
            "Course",
            "project preferences",
            "partner preferences",
            "Dev Experience",
            "Git Experience",
            "Scrum Experience",
            "Management Interest",
            "Non-dutch",
            "Availablility timeslots",
            "Has problems with signing an NDA",
            "Registration Comments",
        ]

        # Get current registration
        current_registration = Registrations.objects.current_registration()

        # Get all submissions for the users in the queryset
        submissions = RegistrationSubmission.objects.filter(
            participant__in=queryset, registration=current_registration
        )

        # Get all unique questions that appear in answers for these submissions
        dynamic_questions = (
            Question.objects.filter(
                registration=current_registration,
                answer__submission__in=submissions,
            )
            .exclude(
                label__in=[
                    "projects",
                    "partners",
                    "devexp",
                    "gitexp",
                    "scrumexp",
                    "management",
                    "nondutch",
                    "timeslots",
                    "nonda",
                    "comments",
                    "first_name",
                    "last_name",
                    "email",
                    "student_number",
                    "course",
                ]
            )
            .distinct()
            .order_by("id")
        )

        # Write header row
        headers = static_headers + [q.question for q in dynamic_questions]
        writer.writerow(headers)

        for user in queryset:
            submission = user.registrationsubmission_set.filter(
                registration=current_registration
            ).first()

            if not submission:
                continue

            static_row = [
                user.first_name,
                user.last_name,
                user.student_number,
                user.github_username,
                submission.course,
                submission.get_answer("projects"),
                submission.get_answer("partners"),
                submission.get_answer("devexp"),
                submission.get_answer("gitexp"),
                submission.get_answer("scrumexp"),
                submission.get_answer("management"),
                submission.get_answer("nondutch"),
                self.convert_timeslots(submission.get_answer("timeslots")),
                submission.get_answer("nonda"),
                submission.get_answer("comments"),
            ]

            # Add dynamic question answers
            dynamic_row = []
            for question in dynamic_questions:
                try:
                    answer = submission.answer_set.get(question=question)
                    dynamic_row.append(answer.answer_value)
                except Answer.DoesNotExist:
                    dynamic_row.append("")

            writer.writerow(static_row + dynamic_row)

        response = HttpResponse(
            content.getvalue(), content_type="application/x-zip-compressed"
        )
        response["Content-Disposition"] = (
            "attachment; filename=registrations.csv"
        )
        return response

    def unassign_from_project(self, request, queryset):
        """Clear the set project for a registration."""
        num_unassigned = 0
        for user in queryset:
            submission = user.registrationsubmission_set.first()
            if submission:
                submission.remove_projects()
                submission.save()
                num_unassigned += 1
        messages.success(
            request,
            f"Succesfully unassigned {num_unassigned} registrations.",
        )

    def get_urls(self):
        """Get admin urls."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(
                    ImportAssignmentAdminView.as_view()
                ),
                name="import",
            ),
        ]
        return custom_urls + urls


class CsvImportForm(forms.Form):
    """Form used when importing a csv group assignment."""

    csv_file = forms.FileField(required=True)
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(), required=True
    )


class ImportAssignmentAdminView(View):
    """Import a CSV file with project assignment."""

    def get(self, request):
        """Get a form to select the semester to import for."""
        form = CsvImportForm()
        payload = {
            "form": form,
            "header": CSV_STRUCTURE[:5],
            "title": "Import",
        }

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
                project = Project.objects.get(
                    name=csv_project, semester=semester
                )
            except Project.DoesNotExist:
                raise ValueError(
                    f"No project was found for {csv_project} in semester {semester}."
                )

            try:
                submission = RegistrationSubmission.objects.get(
                    participant__first_name=csv_first_name,
                    participant__last_name=csv_last_name,
                    participant__student_number=csv_student_number,
                    registration__semester=semester,
                    course__name=csv_course,
                )

            except RegistrationSubmission.DoesNotExist:
                raise ValueError(
                    f"No registration was found for {csv_first_name} {csv_last_name} with student number "
                    f"{csv_student_number} in semester {semester} for course {csv_course}. "
                )

            if submission.get_projects().count() != 0:
                num_ignored += 1
            else:
                submission.add_project(project)
                submission.save()
                num_assigned += 1

        return num_assigned, num_ignored

    def post(self, request):
        """Import and process a .csv file with assigned projects."""
        csv_file = request.FILES["csv_file"]
        semester = Semester.objects.get(pk=request.POST.get("semester"))
        if not csv_file.name.endswith(".csv"):
            messages.error(request, "File is not CSV type")
        elif csv_file.multiple_chunks():
            messages.error(
                request,
                "Uploaded file is too big (%.2f MB)."
                % (csv_file.size / (1000 * 1000),),
            )
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

    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(), required=True
    )
