from django import forms
from .models import Question
from django.contrib.auth.models import User

class PeerReviewForm(forms.Form):
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        global_questions = Question.objects.filter(about_someone_else=False)
        peer_questions = Question.objects.filter(about_someone_else=True)
        if user : 
            peers = User.objects.exclude(pk=user.pk)
        else:
            peers = User.objects.all()

        for q in global_questions:
            field_name = f"{q.pk}"
            self._init_question(q,field_name)
        for peer in peers:
            for q in peer_questions:
                field_name = f"{peer.username}_{q.pk}"
                self._init_question(q,field_name, peer)

    def _init_question(self, question, field_name, peer=None):
        if question.question_type == 'o' :
            self.fields[field_name] = forms.CharField(
                    label=question.question,
                    )
        elif question.closed_question():
            CHOICES = question.choices()
            self.fields[field_name] = forms.ChoiceField(
                    label=question.question,
                    widget=forms.RadioSelect,
                    choices=CHOICES)

        if peer:
            self.fields[field_name].help_text=f"Peer review for {peer.first_name} {peer.last_name}",

