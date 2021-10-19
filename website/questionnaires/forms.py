from bootstrap4.widgets import RadioSelectButtonGroup

from django import forms
from django.forms import ValidationError

from questionnaires.models import QuestionnaireSubmission


class QuestionnaireForm(forms.Form):
    """Dynamic form generating a questionnaires form."""

    def __init__(self, participant, questionnaire, peers, no_peers_warning, check_required=False, *args, **kwargs):
        """Dynamically setup form."""
        super().__init__(*args, **kwargs)

        self.check_required = check_required

        try:
            self.submission = QuestionnaireSubmission.objects.get(
                participant=participant, questionnaire=questionnaire, submitted=False
            )
        except QuestionnaireSubmission.DoesNotExist:
            self.submission = None

        self.participant = participant
        self.questionnaire = questionnaire
        self.questions = questionnaire.question_set.order_by("pk")
        self.peers = peers
        self.no_peers_warning = no_peers_warning

        for question in self.questions:
            if question.about_team_member:
                peers_question = self.peers
            else:
                peers_question = (None,)

            for peer in peers_question:
                self._build_form_field(self.get_field_name(question, peer), question, peer)
                if question.is_closed and question.with_comments:
                    self._build_form_field(
                        self.get_field_name(question, peer, comments=True), question, peer, is_comments=True
                    )

    def clean(self):
        """Validate that the questionnaire is not yet answered."""
        try:
            QuestionnaireSubmission.objects.get(
                participant_id=self.participant.id, questionnaire_id=self.questionnaire.id, submitted=True
            )
        except QuestionnaireSubmission.DoesNotExist:
            pass
        else:
            raise ValidationError("Questionnaire already submitted.", code="invalid")

    def _build_form_field(self, field_name, question, peer=None, is_comments=False):
        if question.is_closed and not is_comments:
            self.fields[field_name] = forms.TypedChoiceField(
                label=question.question,
                widget=RadioSelectButtonGroup,
                choices=question.get_likert_choices(),
                coerce=int,
                empty_value=None,
            )
        else:
            self.fields[field_name] = forms.CharField(
                label=question.question,
                widget=forms.Textarea(
                    attrs={"rows": 4, "placeholder": ""},
                ),
            )

        if not self.check_required or (question.optional or is_comments):
            # Mark all questions as not required, to allow intermediate saves
            self.fields[field_name].required = False
            self.fields[field_name].widget.is_required = False

        if question.optional or is_comments:
            self.fields[field_name].help_text = "Optional"

        if self.submission:
            # Set the initial value for a field if a submission already exists
            answer = self.submission.answer_set.filter(question=question, peer=peer).first()
            self.fields[field_name].initial = answer.answer.value if answer else None

        if peer is not None:
            self.fields[field_name].peer = f"{peer.get_full_name()}"

        self.fields[field_name].is_comments_field = is_comments

    @staticmethod
    def get_field_name(question, peer=None, comments=False):
        """Generate the name of a field used in the HTML to identify a question."""
        if peer is not None:
            if comments:
                return f"question-{question.pk}-{peer.pk}-comments"
            return f"question-{question.pk}-{peer.pk}"
        if comments:
            return f"question-{question.pk}-comments"
        return f"question-{question.pk}"
