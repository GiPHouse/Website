import csv
from io import StringIO

from admin_totals.admin import ModelAdminTotals

from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.utils import model_ngettext
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.utils.encoding import force_text

from courses.models import Semester

from questionnaires.filters import (
    AnswerAdminParticipantFilter,
    AnswerAdminPeerFilter,
    AnswerAdminProjectFilter,
    AnswerAdminQuestionFilter,
    AnswerAdminQuestionnaireFilter,
    AnswerAdminSemesterFilter,
    SubmissionAdminParticipantFilter,
    SubmissionAdminPeerFilter,
    SubmissionAdminProjectFilter,
    SubmissionAdminQuestionnaireFilter,
    SubmissionAdminSemesterFilter,
)
from questionnaires.models import Answer, Question, Questionnaire, QuestionnaireSubmission

from registrations.models import Employee

User: Employee = get_user_model()


class QuestionInline(admin.TabularInline):
    """Inline form element for Questionnaire."""

    model = Question


class AnswerInline(admin.TabularInline):
    """
    Answer model admin inline.

    This allows the admin to show answers together in their respective submissions.
    """

    model = Answer
    can_delete = False
    readonly_fields = ("question", "peer", "answer_display", "comments_display")
    extra = 0
    ordering = ["peer", "question"]

    def answer_display(self, obj):
        """Return answer value for closed questions."""
        if obj.question.is_closed:
            return obj.answer if obj.answer else ""
        return ""

    answer_display.short_description = "answer"

    def comments_display(self, obj):
        """Return comments data or answer data for open questions."""
        if obj.question.is_closed:
            return obj.comments if obj.comments else ""
        return obj.answer if obj.answer else ""

    comments_display.short_description = "comments"

    def has_add_permission(self, request, obj=None):
        """Disable changing answers in the admin."""
        return False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Question model admin."""

    search_fields = ("question",)
    list_display = ("question", "questionnaire")


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    """Questionnaire model admin."""

    inlines = (QuestionInline,)
    search_fields = ("title",)

    actions = ("duplicate_questionnaires", "download_emails_for_employees_without_submission")

    def duplicate_questionnaires(self, request, queryset):
        """Duplicate a questionnaire and all its questions into a new questionnaire."""
        for old_questionnaire in queryset:
            new_questionnaire = Questionnaire.objects.get(pk=old_questionnaire.pk)
            new_questionnaire.pk = None
            new_questionnaire.semester = Semester.objects.get_or_create_current_semester()
            new_questionnaire.save()

            for old_question in old_questionnaire.question_set.all():
                new_question = Question.objects.get(pk=old_question.pk)
                new_question.pk = None
                new_question.questionnaire = new_questionnaire
                new_question.save()

            self.message_user(
                request,
                "Successfully duplicated %(count)d %(items)s. Do not forget to update the availability deadlines!"
                % {"count": len(queryset), "items": model_ngettext(self.opts, len(queryset))},
                messages.SUCCESS,
            )

    def download_emails_for_employees_without_submission(self, request, queryset):
        """Export the email addresses of employees that did not submit for the questionnaire to a .TXT file."""
        content = StringIO()

        for q in queryset:
            employees = Employee.objects.filter(registration__semester=q.semester).exclude(
                pk__in=q.questionnairesubmission_set.filter(submitted=True).values("pk")
            )
            emails = ", ".join(employees.values_list("email", flat=True))
            content.write(f"No submission for {q}:\n\n")
            content.write(emails)
            content.write("\n\n\n\n")

        response = HttpResponse(content.getvalue(), content_type="text/plain")
        response["Content-Disposition"] = "attachment; filename=not-submitted.txt"
        return response


class SubmittedSubmissionsFilter(SimpleListFilter):
    """Filter for submitted and un-submitted questionnaire submissions."""

    title = "submitted"
    parameter_name = "un-submitted"

    def lookups(self, request, model_admin):
        """Filter values."""
        return ((True, "Include un-submitted"),)

    def choices(self, changelist):
        """Override the default value to display only submitted."""
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string({}, [self.parameter_name]),
            "display": "Only submitted",
        }
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == force_text(lookup),
                "query_string": changelist.get_query_string({self.parameter_name: lookup}, []),
                "display": title,
            }

    def queryset(self, request, queryset):
        """Filter the queryset."""
        return queryset if self.value() is not None else queryset.filter(submitted=True)


@admin.register(QuestionnaireSubmission)
class QuestionnaireSubmissionAdmin(admin.ModelAdmin):
    """QuestionnaireSubmission model admin."""

    actions = ("export_submissions",)

    inlines = (AnswerInline,)

    list_display = ("questionnaire", "participant_name", "on_time")
    list_filter = (
        SubmittedSubmissionsFilter,
        SubmissionAdminSemesterFilter,
        SubmissionAdminQuestionnaireFilter,
        SubmissionAdminParticipantFilter,
        SubmissionAdminPeerFilter,
        SubmissionAdminProjectFilter,
        "late",
    )

    def participant_name(self, obj):
        """Return the full name of the participant."""
        return obj.participant.get_full_name()

    participant_name.short_description = "Participant"
    participant_name.admin_order_field = "participant__first_name"

    def on_time(self, obj):
        """Return whether the answer was submitted late or on time."""
        return not obj.late

    on_time.boolean = True
    on_time.short_description = "On Time"
    on_time.admin_order_field = "late"

    def export_submissions(self, request, queryset):
        """Export selected submissions to a CSV file."""
        content = StringIO()
        writer = csv.writer(content, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(
            ["Questionnaire", "Participant", "Late", "Question", "Peer", "Answer (as text)", "Answer (as number)"]
        )

        for submission in queryset:
            for answer in submission.answer_set.all():

                writer.writerow(
                    [
                        answer.submission.questionnaire,
                        answer.submission.participant,
                        answer.submission.late,
                        answer.question.question,
                        answer.peer,
                        answer.answer.get_value_display() if answer.question.is_closed else answer.answer.value,
                        answer.answer.value if answer.question.is_closed else "",
                    ]
                )

        response = HttpResponse(content.getvalue(), content_type="application/x-zip-compressed")
        response["Content-Disposition"] = "attachment; filename=submissions.csv"
        return response


class SubmittedSubmissionsAnswerFilter(SubmittedSubmissionsFilter):
    """Filter for submitted and un-submitted questionnaire answers."""

    def queryset(self, request, queryset):
        """Filter the queryset."""
        return queryset if self.value() is not None else queryset.filter(submission__submitted=True)


@admin.register(Answer)
class AnswerAdmin(ModelAdminTotals):
    """Answer model admin."""

    list_filter = (
        SubmittedSubmissionsAnswerFilter,
        AnswerAdminSemesterFilter,
        AnswerAdminQuestionnaireFilter,
        AnswerAdminQuestionFilter,
        AnswerAdminProjectFilter,
        AnswerAdminParticipantFilter,
        AnswerAdminPeerFilter,
        "submission__late",
    )

    readonly_fields = ("answer",)

    list_display = (
        "question",
        "participant_name",
        "peer_name",
        "answer_display",
        "comments_display",
        "on_time",
        "questionnaire",
    )

    list_totals = [
        (
            "answer_display",
            lambda field: Avg(Coalesce("qualityanswerdata__value", 0) + Coalesce("agreementanswerdata__value", 0)),
        ),
    ]

    actions = ("export_answers",)

    def participant_name(self, obj):
        """Return the full name of the participant."""
        return obj.submission.participant.get_full_name()

    participant_name.short_description = "Participant"
    participant_name.admin_order_field = "submission__participant__first_name"

    def peer_name(self, obj):
        """Return the full name of the peer (if one exists)."""
        if obj.peer is not None:
            return obj.peer.get_full_name()

    peer_name.short_description = "Peer"
    peer_name.admin_order_field = "peer"

    def on_time(self, obj):
        """Return whether the answer was submitted late or on time."""
        return not obj.submission.late

    on_time.boolean = True
    on_time.short_description = "On Time"
    on_time.admin_order_field = "submission__late"

    def questionnaire(self, obj):
        """Return the title of the corresponding questionnaire."""
        return obj.submission.questionnaire.title

    questionnaire.short_description = "Questionnaire"
    questionnaire.admin_order_field = "submission__questionnaire"

    def answer_display(self, obj):
        """Return answer value for closed questions."""
        if obj.question.is_closed:
            return obj.answer if obj.answer else ""
        return ""

    answer_display.short_description = "answer"

    def comments_display(self, obj):
        """Return comments data or answer data for open questions."""
        if obj.question.is_closed:
            return obj.comments if obj.comments else ""
        return obj.answer if obj.answer else ""

    comments_display.short_description = "comments"

    def export_answers(self, request, queryset):
        """Export selected answers to a CSV file."""
        content = StringIO()
        writer = csv.writer(content, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(
            ["Questionnaire", "Participant", "Late", "Question", "Peer", "Answer (as text)", "Answer (as number)"]
        )

        for answer in queryset:

            writer.writerow(
                [
                    answer.submission.questionnaire,
                    answer.submission.participant,
                    answer.submission.late,
                    answer.question.question,
                    answer.peer,
                    answer.answer.get_value_display() if answer.question.is_closed else answer.answer.value,
                    answer.answer.value if answer.question.is_closed else "",
                ]
            )

        response = HttpResponse(content.getvalue(), content_type="application/x-zip-compressed")
        response["Content-Disposition"] = "attachment; filename=submissions.csv"
        return response

    class Media:
        """Custom styling."""

        css = {"all": ("admin/questionnaires/css/custom-answer-admin.css",)}
