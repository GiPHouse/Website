from admin_auto_filters.filters import AutocompleteFilter

from projects.models import Project

from questionnaires.models import Answer, Questionnaire, QuestionnaireSubmission

from registrations.models import Registration


class SubmissionAdminSemesterFilter(AutocompleteFilter):
    """Filter class to filter Semester objects."""

    title = "Semester"
    field_name = "semester"
    rel_model = Questionnaire

    def queryset(self, request, queryset):
        """Filter semesters."""
        if self.value():
            return queryset.filter(questionnaire__semester=self.value())
        return queryset


class SubmissionAdminQuestionnaireFilter(AutocompleteFilter):
    """Filter class to filter Questionnaire objects."""

    title = "Questionnaire"
    field_name = "questionnaire"


class SubmissionAdminProjectFilter(AutocompleteFilter):
    """Filter class to filter Project objects."""

    title = "Projects"
    field_name = "projects"
    rel_model = Registration

    def lookups(self, request, model_admin):
        """List the projects."""
        return ((project.id, project.name) for project in Project.objects.all())

    def queryset(self, request, queryset):
        """Filter out participants in the specified Project."""
        if self.value():
            return queryset.filter(participant__registration__projects=self.value())
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
        return queryset


class AnswerAdminQuestionFilter(AutocompleteFilter):
    """Filter class to filter Question objects."""

    title = "Question"
    field_name = "question"


class AnswerAdminProjectFilter(AutocompleteFilter):
    """Filter class to filter Project objects."""

    title = "Projects"
    field_name = "projects"
    rel_model = Registration

    def lookups(self, request, model_admin):
        """List the projects."""
        return ((project.id, project.name) for project in Project.objects.all())

    def queryset(self, request, queryset):
        """Filter out participants in the specified Project."""
        if self.value():
            return queryset.filter(submission__participant__registration__projects=self.value())
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
        return queryset
