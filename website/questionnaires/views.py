from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from courses.models import Semester

from giphousewebsite.mixins import LoginRequiredMessageMixin

from questionnaires.forms import QuestionnaireForm
from questionnaires.models import Answer, Questionnaire, QuestionnaireSubmission

User: DjangoUser = get_user_model()


class OverviewView(LoginRequiredMessageMixin, TemplateView):
    """List the available questionnaires."""

    template_name = "questionnaires/overview.html"

    def get_context_data(self, **kwargs):
        """Add the current questionnaires and submissions to the context of the view."""
        context = super().get_context_data()

        context["submissions"] = []
        context["questionnaires"] = []
        for questionnaire in Questionnaire.objects.current_questionnaires():

            try:
                context["submissions"].append(
                    QuestionnaireSubmission.objects.get(questionnaire=questionnaire, participant=self.request.user)
                )
            except QuestionnaireSubmission.DoesNotExist:
                context["questionnaires"].append(questionnaire)

        return context


class QuestionnaireView(LoginRequiredMessageMixin, FormView):
    """A dynamically generated FormView."""

    template_name = "questionnaires/questionnaire.html"
    form_class = QuestionnaireForm

    def get_form_kwargs(self):
        """Add extra information to the form."""
        kwargs = super().get_form_kwargs()

        participant = self.request.user
        kwargs["participant"] = participant

        questionnaire = get_object_or_404(Questionnaire, pk=self.kwargs["questionnaire"])
        if questionnaire.is_closed:
            raise Http404
        kwargs["questionnaire"] = questionnaire
        kwargs["peers"] = User.objects.exclude(pk=participant.pk).filter(
            groups__in=participant.groups.filter(project__semester=Semester.objects.get_current_semester())
        )
        kwargs["no_peers_warning"] = (
            questionnaire.question_set.filter(about_team_member=True).exists() and not kwargs["peers"]
        )

        return kwargs

    def form_valid(self, form):
        """Validate the form."""
        submission = QuestionnaireSubmission.objects.create(
            questionnaire=form.questionnaire, participant=self.request.user
        )

        for question in form.questions:

            if question.about_team_member:
                peers = form.peers
            else:
                peers = (None,)

            for peer in peers:
                field_name = QuestionnaireForm.get_field_name(question, peer)
                answer = Answer.objects.create(submission=submission, peer=peer, question=question)
                answer.answer = form.cleaned_data[field_name]

        messages.success(self.request, "Questionnaire successfully submitted!", extra_tags="success")
        return redirect("home")
