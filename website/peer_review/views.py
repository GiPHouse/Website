from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic.edit import FormView

from .models import Answer, Question
from .forms import PeerReviewForm


class PeerReviewView(FormView):
    """A dynamically generated FormView."""

    template_name = 'peer_review_form.html'
    form_class = PeerReviewForm

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        form_class = self.get_form_class()
        # Supply the current logged in user to the form
        return form_class(self.request.user, **self.get_form_kwargs())

    def form_valid(self, form):
        """Validate the form."""
        participant = self.request.user
        peers = User.objects.exclude(pk=participant.pk)
        questions = Question.objects.all()

        for question in questions:
            if question.about_team_member:
                for peer in peers:
                    field_name = f"{peer.username}_{question.pk}"
                    Answer.objects.create(
                        participant=participant,
                        peer=peer,
                        question=question,
                        answer=form.cleaned_data[field_name],
                    )
            else:
                field_name = f"{question.pk}"
                Answer.objects.create(
                    participant=participant,
                    question=question,
                    peer=None,
                    answer=form.cleaned_data[field_name],
                )

        messages.success(self.request, "Peer review succesfully submitted!", extra_tags='alert alert-success')
        return redirect("home")
