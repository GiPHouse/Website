from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from courses.models import Semester

from giphousewebsite.mixins import LoginRequiredMessageMixin

from projects.models import Project

from questionnaires.forms import QuestionnaireForm
from questionnaires.models import Answer, Questionnaire, QuestionnaireSubmission

from registrations.models import Employee, Registration

User: Employee = get_user_model()


class OverviewView(LoginRequiredMessageMixin, TemplateView):
    """List the available questionnaires."""

    template_name = "questionnaires/overview.html"

    def get_context_data(self, **kwargs):
        """Add the current questionnaires and submissions to the context of the view."""
        context = super().get_context_data()

        context["submissions"] = []
        context["open_questionnaires"] = []
        context["questionnaires_in_progress"] = []
        for questionnaire in Questionnaire.objects.current_questionnaires():

            try:
                context["submissions"].append(
                    QuestionnaireSubmission.objects.get(
                        questionnaire=questionnaire, participant=self.request.user, submitted=True
                    )
                )
            except QuestionnaireSubmission.DoesNotExist:
                context["questionnaires_in_progress"].append(questionnaire) if QuestionnaireSubmission.objects.filter(
                    questionnaire=questionnaire, participant=self.request.user, submitted=False
                ).exists() else context["open_questionnaires"].append(questionnaire)

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

        try:
            participant_project = Project.objects.get(
                registration__user=participant, semester=Semester.objects.get_or_create_current_semester()
            )
        except Project.DoesNotExist:
            kwargs["peers"] = []
        else:
            project_registrations = Registration.objects.filter(project=participant_project)
            kwargs["peers"] = User.objects.exclude(pk=participant.pk).filter(registration__in=project_registrations)

        kwargs["no_peers_warning"] = (
            questionnaire.question_set.filter(about_team_member=True).exists() and not kwargs["peers"]
        )

        return kwargs

    def form_valid(self, form):
        """Validate the form."""
        if "submit" in self.request.POST:
            # Re-evaluate the form to check required fields
            form_check_required_fields = QuestionnaireForm(**self.get_form_kwargs(), check_required=True)
            if not form_check_required_fields.is_valid():
                form._errors = form_check_required_fields.errors
                return self.form_invalid(form)

            submission, _ = QuestionnaireSubmission.objects.get_or_create(
                questionnaire=form.questionnaire, participant=self.request.user, submitted=True
            )
        else:
            submission, _ = QuestionnaireSubmission.objects.get_or_create(
                questionnaire=form.questionnaire, participant=self.request.user, submitted=False
            )

        for question in form.questions:

            if question.about_team_member:
                peers = form.peers
            else:
                peers = (None,)

            for peer in peers:
                field_name = QuestionnaireForm.get_field_name(question, peer)
                answer, _ = Answer.objects.get_or_create(submission=submission, peer=peer, question=question)
                answer.answer = form.cleaned_data[field_name]
                if question.with_comments:
                    answer.comments = form.cleaned_data[
                        QuestionnaireForm.get_field_name(question, peer, comments=True)
                    ]

        if submission.submitted:
            messages.success(self.request, "Questionnaire successfully submitted!", extra_tags="success")
            return redirect("home")
        else:
            messages.info(self.request, "Questionnaire saved", extra_tags="info")
            return self.render_to_response(self.get_context_data())
