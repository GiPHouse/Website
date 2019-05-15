from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin

from courses.models import Semester

from projects.models import Project

from questionnaires.models import Answer, Question, Questionnaire, QuestionnaireSubmission


class DecimalFilter(admin.SimpleListFilter):
    """Filter class to filter specific decimal input."""

    template = 'questionnaires/admin/decimal_filter.html'

    def lookups(self, *args):
        """Implement necessary method."""
        return ()

    def has_output(self):
        """Tell Django to always show this filter."""
        return True

    def value(self):
        """Convert the specified value to a float."""
        value = super().value()

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def choices(self, changelist):
        """
        Specify context variables.

        Instead of sending actual choices, we use this method more like a `get_context_data` method.
        Normally, this method specifies all the possible choices.
        Because the user specifies their own input, we do not have a set of choices.
        We, however, do have a lot of info that needs to be passed to the template to accomplish this.
        That is why, instead of specifying choices, we specify context in this method.
        """
        return (
            {
                'get_query': changelist.params,
                'parameter_name': self.parameter_name,
                'help_text': self.help_text,
                'current_value': self.value(),
                'all': {
                    'selected': self.value() is None,
                    'query_string': changelist.get_query_string(remove=[self.parameter_name]),
                },
            },
        )


class SubmissionAdminSemesterFilter(AutocompleteFilter):
    """Filter class to filter Semester objects."""

    title = 'Semester'
    field_name = 'semester'
    rel_model = Questionnaire

    def queryset(self, request, queryset):
        """Filter semesters."""
        if self.value():
            return queryset.filter(questionnaire__semester=self.value())
        else:
            return queryset


class SubmissionAdminAverageFilter(DecimalFilter):
    """Filter class to filter peer averages."""

    title = 'Below Peer Average'
    parameter_name = 'below_peer_average'
    help_text = 'Closed question average of peer below x.'

    def queryset(self, request, queryset):
        """Return all submission that contain a peer average below the specified value."""
        value = self.value()

        if value is None:
            return queryset

        ids = [
            submission.id
            for submission in queryset
            if self._peer_average_below_threshold(submission, value)
        ]
        return queryset.filter(id__in=ids)

    @staticmethod
    def _peer_average_below_threshold(submission, threshold):
        """
        Calculate whether this submission has a peer average below the threshold.

        Calculate the average of the numerical values of all answers to closed questions for each peer
        in this submission. If an average is below the threshold, return True.
        :param threshold:
        :return: Whether the average is below the threshold.
        """
        peers = submission.answer_set.filter(peer__isnull=False).values_list('peer_id', flat=True)

        for peer_id in peers:
            closed_answer_data = [
                answer.answer.value
                for answer in submission.answer_set
                                        .filter(peer_id=peer_id)
                                        .exclude(question__question_type=Question.OPEN)
                if answer.question.is_closed
            ]

            if closed_answer_data and sum(closed_answer_data)/len(closed_answer_data) <= threshold:
                return True

        return False


class SubmissionAdminQuestionnaireFilter(AutocompleteFilter):
    """Filter class to filter Questionnaire objects."""

    title = 'Questionnaire'
    field_name = 'questionnaire'


class SubmissionAdminProjectFilter(admin.SimpleListFilter):
    """Filter class to filter current Project objects."""

    title = 'Current Projects'
    parameter_name = 'project'

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

    title = 'Participant'
    field_name = 'participant'


class SubmissionAdminPeerFilter(AutocompleteFilter):
    """Filter class to filter peers."""

    title = 'Peer'
    field_name = 'peer'
    rel_model = Answer

    def queryset(self, request, queryset):
        """Filter the specified peer."""
        if self.value():
            return queryset.filter(answer__peer=self.value())
        else:
            return queryset


class AnswerAdminQuestionnaireFilter(AutocompleteFilter):
    """Filter class to filter Questionnaire objects."""

    title = 'Questionnaire'
    field_name = 'questionnaire'
    rel_model = QuestionnaireSubmission

    def queryset(self, request, queryset):
        """Filter the specified Questionnaire object."""
        if self.value():
            return queryset.filter(submission__questionnaire=self.value())
        else:
            return queryset


class AnswerAdminQuestionFilter(AutocompleteFilter):
    """Filter class to filter Question objects."""

    title = 'Question'
    field_name = 'question'


class AnswerAdminProjectFilter(admin.SimpleListFilter):
    """Filter class to filter current Project objects."""

    title = 'Current Projects'
    parameter_name = 'project'

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

    title = 'Participant'
    field_name = 'participant'
    rel_model = QuestionnaireSubmission

    def queryset(self, request, queryset):
        """Filter participants."""
        if self.value():
            return queryset.filter(submission__participant=self.value())
        else:
            return queryset


class AnswerAdminPeerFilter(AutocompleteFilter):
    """Filter class to filter peers."""

    title = 'Peer'
    field_name = 'peer'


class AnswerAdminValueFilter(DecimalFilter):
    """Filter class to filter closed question answer values."""

    title = 'Value Below Peer Answer'
    parameter_name = 'below_peer'
    help_text = 'Closed question of peer below x.'

    def queryset(self, request, queryset):
        """Filter all closed question answers below the specified value."""
        value = self.value()

        if value is None:
            return queryset

        ids = [
            answer.id
            for answer in queryset.exclude(question__question_type=Question.OPEN).exclude(peer__isnull=True)
            if answer.answer.value <= value
        ]

        return queryset.filter(id__in=ids)


class AnswerAdminSemesterFilter(AutocompleteFilter):
    """Filter class to filter Semester objects."""

    title = 'Semester'
    field_name = 'semester'
    rel_model = Questionnaire

    def queryset(self, request, queryset):
        """Filter semesters."""
        if self.value():
            return queryset.filter(submission__questionnaire__semester=self.value())
        else:
            return queryset
