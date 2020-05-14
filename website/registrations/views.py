from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView

from courses.models import Semester


from registrations.forms import Step2Form
from registrations.models import Employee, Registration

User: Employee = get_user_model()


class Step1View(TemplateView):
    """View showing GitHub link."""

    template_name = "registrations/step-1.html"

    def get_context_data(self, *args, **kwargs):
        """Add semester to register form."""
        return super().get_context_data(
            registration_semester=Semester.objects.get_first_semester_with_open_registration(), **kwargs
        )

    def dispatch(self, request, *args, **kwargs):
        """Check whether user is authenticated and if registration is possible."""
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in", extra_tags="success")
            return redirect("home")

        if not Semester.objects.get_first_semester_with_open_registration():
            messages.warning(request, "Registrations are currently not open", extra_tags="danger")
            return redirect("home")

        return super().dispatch(request, *args, **kwargs)


class Step2View(FormView):
    """View to show Step2Form."""

    template_name = "registrations/step-2.html"

    form_class = Step2Form
    success_url = "/"

    def dispatch(self, request, *args, **kwargs):
        """Check whether github_id is set in the session."""
        if not self.request.session.get("github_id"):
            return HttpResponseBadRequest()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add semester to register form."""
        return super().get_context_data(
            registration_semester=Semester.objects.get_first_semester_with_open_registration(), **kwargs
        )

    def get_initial(self):
        """Get the initial data for the form."""
        initial = super(Step2View, self).get_initial()

        try:
            first_name, last_name = self.request.session["github_name"].rsplit(" ", 1)
        except (KeyError, AttributeError):
            first_name, last_name = "", ""
        except ValueError:
            first_name, last_name = self.request.session["github_name"], ""

        initial.update(
            {
                "email": self.request.session.get("github_email") or "",
                "github_id": self.request.session.get("github_id") or "",
                "github_username": self.request.session.get("github_username") or "",
                "first_name": first_name,
                "last_name": last_name,
            }
        )

        return initial

    def form_valid(self, form):
        """Register new user if the form is valid."""
        with transaction.atomic():
            user, _ = User.objects.get_or_create(github_id=self.request.session["github_id"])

            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.github_username = form.cleaned_data["github_username"]
            user.student_number = form.cleaned_data["student_number"]
            user.save()

            Registration.objects.create(
                user=user,
                semester=Semester.objects.get_first_semester_with_open_registration(),
                course=form.cleaned_data["course"],
                experience=form.cleaned_data["experience"],
                preference1=form.cleaned_data["project1"],
                preference2=form.cleaned_data["project2"],
                preference3=form.cleaned_data["project3"],
                partner_preference1=form.cleaned_data["partner1"],
                partner_preference2=form.cleaned_data["partner2"],
                partner_preference3=form.cleaned_data["partner3"],
                comments=form.cleaned_data["comments"],
                education_background=form.cleaned_data["background"],
            )

        del self.request.session["github_id"]
        del self.request.session["github_username"]
        del self.request.session["github_name"]
        del self.request.session["github_email"]

        messages.success(self.request, "Registration created successfully", extra_tags="success")

        login(self.request, user, backend="github_oauth.backends.GithubOAuthBackend")

        return redirect("home")
