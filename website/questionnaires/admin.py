from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser

from questionnaires.filters import (
    AnswerAdminParticipantFilter,
    AnswerAdminPeerFilter,
    AnswerAdminProjectFilter,
    AnswerAdminQuestionFilter,
    AnswerAdminQuestionnaireFilter,
    AnswerAdminSemesterFilter,
    AnswerAdminValueFilter,
    SubmissionAdminAverageFilter,
    SubmissionAdminParticipantFilter,
    SubmissionAdminPeerFilter,
    SubmissionAdminProjectFilter,
    SubmissionAdminQuestionnaireFilter,
    SubmissionAdminSemesterFilter
)
from questionnaires.models import Answer, Question, Questionnaire, QuestionnaireSubmission

User: DjangoUser = get_user_model()


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
    readonly_fields = ('question', 'peer', 'answer',)
    extra = 0
    ordering = ['peer', 'question']

    def has_add_permission(self, request, obj=None):
        """Disable changing answers in the admin."""
        return False


@admin.register(Question)
class Question(admin.ModelAdmin):
    """Question model admin."""

    search_fields = ('question',)
    list_display = ('question', 'questionnaire')


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    """Questionnaire model admin."""

    inlines = (QuestionInline,)
    search_fields = ('title',)


@admin.register(QuestionnaireSubmission)
class QuestionnaireSubmissionAdmin(admin.ModelAdmin):
    """QuestionnaireSubmission model admin."""

    inlines = (AnswerInline,)

    list_display = ('questionnaire', 'participant_name', 'on_time')
    list_filter = (SubmissionAdminSemesterFilter, SubmissionAdminQuestionnaireFilter, SubmissionAdminParticipantFilter,
                   SubmissionAdminPeerFilter, SubmissionAdminProjectFilter, 'late', SubmissionAdminAverageFilter)

    def participant_name(self, obj):
        """Return the full name of the participant."""
        return obj.participant.get_full_name()
    participant_name.short_description = 'Participant'
    participant_name.admin_order_field = 'participant__first_name'

    def on_time(self, obj):
        """Return whether the answer was submitted late or on time."""
        return not obj.late
    on_time.boolean = True
    on_time.short_description = 'On Time'
    on_time.admin_order_field = 'late'

    class Media:
        """Necessary to use AutocompleteFilter."""


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Answer model admin."""

    list_filter = (AnswerAdminSemesterFilter, AnswerAdminQuestionnaireFilter, AnswerAdminQuestionFilter,
                   AnswerAdminProjectFilter, AnswerAdminParticipantFilter, AnswerAdminPeerFilter,
                   'submission__late', AnswerAdminValueFilter)

    readonly_fields = ('answer',)
    list_display = ('questionnaire', 'question', 'participant_name', 'peer_name', 'on_time', 'likert_answer')

    def participant_name(self, obj):
        """Return the full name of the participant."""
        return obj.submission.participant.get_full_name()
    participant_name.short_description = 'Participant'
    participant_name.admin_order_field = 'submission__participant__first_name'

    def peer_name(self, obj):
        """Return the full name of the peer (if one exists)."""
        if obj.peer is not None:
            return obj.peer.get_full_name()
    peer_name.short_description = 'Peer'
    peer_name.admin_order_field = 'peer'

    def on_time(self, obj):
        """Return whether the answer was submitted late or on time."""
        return not obj.submission.late
    on_time.boolean = True
    on_time.short_description = 'On Time'
    on_time.admin_order_field = 'submission__late'

    def questionnaire(self, obj):
        """Return the title of the corresponding questionnaire."""
        return obj.submission.questionnaire.title
    questionnaire.short_description = 'Questionnaire'
    questionnaire.admin_order_field = 'submission__questionnaire'

    def likert_answer(self, obj):
        """Return likert answers."""
        return obj.answer if obj.question.is_closed else str(obj.answer)[:30]+"..."
    likert_answer.short_description = 'Answer'
    likert_answer.short_description = 'answer'

    class Media:
        """Necessary to use AutocompleteFilter."""
