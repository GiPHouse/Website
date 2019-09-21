from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin

from courses.models import Semester

from projects.models import Project

from questionnaires.models import Answer, Questionnaire, QuestionnaireSubmission


class SubmissionAdminSemesterFilter(AutocompleteFilter):
    """Filter class to filter Semester objects."""

    title = "Semester"
    field_name = "semester"
    rel_model = Questionnaire

    def queryset(self, request, queryset):
        """Filter semesters."""
        if self.value():
            return queryset.filter(questionnaire__semester=self.value())
        else:
            return queryset


class SubmissionAdminQuestionnaireFilter(AutocompleteFilter):
    """Filter class to filter Questionnaire objects."""

    title = "Questionnaire"
    field_name = "questionnaire"


class SubmissionAdminProjectFilter(admin.SimpleListFilter):
    """Filter class to filter current Project objects."""

    title = "Current Projects"
    parameter_name = "project"

    def lookups(self, request, model_admin):
        """List the current projects."""
        return (
            (project.id, project.name)
            for project in Project.objects.filter(semester=Semester.objects.get_current_semester())
        )

    def queryset(self, request, queryset):
        """Filter out participants in the specified Project."""
        if self.value():
            return queryset.filter(participant__groups__id=self.value())
        return queryset


class SubmissionAdminParticipantFilter(AutocompleteFilter):
    """Filter class to filter participants."""

    title = "Participant (submitter)"
    field_name = "participant"


class SubmissionAdminPeerFilter(AutocompleteFilter):
    """Filter class to filter peers."""

    title = "Peer"
    field_name = "peer"
    rel_model = Answer

    def queryset(self, request, queryset):
        """Filter the specified peer."""
        if self.value():
            return queryset.filter(answer__peer=self.value()).distinct()
        else:
            return queryset


class AnswerAdminQuestionnaireFilter(AutocompleteFilter):
    """Filter class to filter Questionnaire objects."""

    title = "Questionnaire"
    field_name = "questionnaire"
    rel_model = QuestionnaireSubmission

    def queryset(self, request, queryset):
        """Filter the specified Questionnaire object."""
        if self.value():
            return queryset.filter(submission__questionnaire=self.value())
        else:
            return queryset


class AnswerAdminQuestionFilter(AutocompleteFilter):
    """Filter class to filter Question objects."""

    title = "Question"
    field_name = "question"


class AnswerAdminProjectFilter(admin.SimpleListFilter):
    """Filter class to filter current Project objects."""

    title = "Current Projects"
    parameter_name = "project"

    def lookups(self, request, model_admin):
        """List the current projects."""
        return (
            (project.id, project.name)
            for project in Project.objects.filter(semester=Semester.objects.get_current_semester())
        )

    def queryset(self, request, queryset):
        """Filter out participants in the specified Project."""
        if self.value():
            return queryset.filter(submission__participant__groups__id=self.value())
        return queryset


class AnswerAdminParticipantFilter(AutocompleteFilter):
    """Filter class to filter participants."""

    title = "Participant"
    field_name = "participant"
    rel_model = QuestionnaireSubmission

    def queryset(self, request, queryset):
        """Filter participants."""
        if self.value():
            return queryset.filter(submission__participant=self.value())
        else:
            return queryset


class AnswerAdminPeerFilter(AutocompleteFilter):
    """Filter class to filter peers."""

    title = "Peer"
    field_name = "peer"


class AnswerAdminSemesterFilter(AutocompleteFilter):
    """Filter class to filter Semester objects."""

    title = "Semester"
    field_name = "semester"
    rel_model = Questionnaire

    def queryset(self, request, queryset):
        """Filter semesters."""
        if self.value():
            return queryset.filter(submission__questionnaire__semester=self.value())
        else:
            return queryset
