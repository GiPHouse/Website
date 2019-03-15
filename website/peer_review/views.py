from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, get_list_or_404
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic.edit import FormView

from registrations.models import users_in_same_group
from .models import Answer, Question, Questionnaire
from .forms import PeerReviewForm


class OverviewView(LoginRequiredMixin, ListView):
    """List the available questionnaires."""

    # Raise exception when not logged in
    raise_exception = True
    model = Questionnaire

    def get_queryset(self):
        """Return the available questionnaires queryset."""
        return super().get_queryset().filter(available_from__lte=timezone.now(),
                                             available_until__gte=timezone.now())


class PeerReviewView(LoginRequiredMixin, FormView):
    """A dynamically generated FormView."""

    # Raise exception when not logged in
    raise_exception = True

    template_name = 'peer_review/form.html'
    form_class = PeerReviewForm

    def dispatch(self, request, questionnaire=None, *args, **kwargs):
        """Set up the objects used in this form."""
        self.questionnaire = get_object_or_404(Questionnaire, pk=questionnaire)
        self.participant = self.request.user
        self.peers = get_list_or_404(users_in_same_group(self.participant))
        self.questions = Question.objects.filter(questionnaire=self.questionnaire)
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        form_class = self.get_form_class()
        # Supply the current logged in user to the form
        return form_class(peers=self.peers, questions=self.questions, **self.get_form_kwargs())

    def form_valid(self, form):
        """Validate the form."""
        participant = self.request.user

        for question in self.questions:
            if question.about_team_member:
                for peer in self.peers:
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

        messages.success(self.request, "Peer review successfully submitted!", extra_tags='alert alert-success')
        return redirect("home")
