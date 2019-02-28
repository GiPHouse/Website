from django import forms
from .models import Question
from django.contrib.auth import get_user_model


class PeerReviewForm(forms.Form):
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        questions = Question.objects.all()
        peers = get_user_model().objects.exclude(pk=user.pk)

        for question in questions:
            if question.about_someone_else:
                for peer in peers:
                    field_name = f"{peer.username}_{question.pk}"
                    self._build_form_field(question, field_name, peer)
            else:
                field_name = f"{question.pk}"
                self._build_form_field(question, field_name)

    def _build_form_field(self, question, field_name, peer=None):
        if question.closed_question():
            CHOICES = question.choices()
            self.fields[field_name] = forms.ChoiceField(
                label=question.question,
                widget=forms.RadioSelect,
                choices=CHOICES,
            )
        else:  # question.question_type == 'o':
            self.fields[field_name] = forms.CharField(
                label=question.question,
            )

        if question.about_someone_else and peer:
            self.fields[field_name].help_text = \
                f"Peer review for {peer.first_name} {peer.last_name}"
