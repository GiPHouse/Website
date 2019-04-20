from django import forms
from django.forms import ValidationError

from peer_review.models import QuestionnaireSubmission


class PeerReviewForm(forms.Form):
    """Dynamic form generating a peer review form."""

    def __init__(self, participant, questionnaire, peers, *args, **kwargs):
        """Dynamically setup form."""
        super().__init__(*args, **kwargs)

        self.participant = participant
        self.questionnaire = questionnaire
        self.questions = questionnaire.question_set.all()
        self.peers = peers

        for question in self.questions:

            if question.about_team_member:
                question_peers = self.peers
            else:
                question_peers = (None, )

            for peer in question_peers:
                self._build_form_field(self.get_field_name(question, peer), question, peer)

    def clean(self):
        """Validate that the form is not closed."""
        if self.questionnaire.is_closed:
            raise ValidationError('Questionnaire is closed.', code='invalid')

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
            self.fields[field_name].help_text = f"Peer review for {peer.get_full_name()}"
        else:
            self.fields[field_name].help_text = "General Question"

    @staticmethod
    def get_field_name(question, peer=None):
        """Generate the name of a field used in the HTML to identify a question."""
        if peer is not None:
            return f'question-{question.pk}-{peer.pk}'
        return f'question-{question.pk}'
