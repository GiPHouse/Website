from django import forms
from django.forms import ValidationError

from questionnaires.models import QuestionnaireSubmission


class QuestionnaireForm(forms.Form):
    """Dynamic form generating a questionnaires form."""

    def __init__(self, participant, questionnaire, peers, no_peers_warning, *args, **kwargs):
        """Dynamically setup form."""
        super().__init__(*args, **kwargs)

        self.participant = participant
        self.questionnaire = questionnaire
        self.questions = questionnaire.question_set.all()
        self.peers = peers
        self.no_peers_warning = no_peers_warning

        for question in self.questions:
            if question.about_team_member:
                peers_question = self.peers
            else:
                peers_question = (None, )

            for peer in peers_question:
                self._build_form_field(self.get_field_name(question, peer), question, peer)

    def clean(self):
        """Validate that the form is not closed."""
        try:
            QuestionnaireSubmission.objects.get(
                participant_id=self.participant.id,
                questionnaire_id=self.questionnaire.id
            )
        except QuestionnaireSubmission.DoesNotExist:
            pass
        else:
            raise ValidationError('Questionnaire already submitted.', code='invalid')

    def _build_form_field(self, field_name, question, peer=None):

        if question.is_closed:
            self.fields[field_name] = forms.TypedChoiceField(
                label=question.question,
                widget=forms.RadioSelect(),
                choices=question.get_likert_choices(),
                coerce=int,
                empty_value=None,
            )
        else:
            self.fields[field_name] = forms.CharField(
                label=question.question,
                widget=forms.Textarea(attrs={'rows': 4, 'placeholder': ''})
            )

        if peer is not None:
            self.fields[field_name].help_text = f"{peer.get_full_name()}"
        else:
            self.fields[field_name].help_text = ""

    @staticmethod
    def get_field_name(question, peer=None):
        """Generate the name of a field used in the HTML to identify a question."""
        if peer is not None:
            return f'question-{question.pk}-{peer.pk}'
        return f'question-{question.pk}'
