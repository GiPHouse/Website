from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.models import User as DjangoUser
from django.db import IntegrityError, transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView

from courses.models import Semester


from registrations.forms import Step2Form
from registrations.models import GiphouseProfile, Registration, Role

User: DjangoUser = get_user_model()


class Step1View(TemplateView):
    """View showing GitHub link."""

    template_name = "registrations/step-1.html"

    def dispatch(self, request, *args, **kwargs):
        """Check whether user is authenticated and if registration is possible."""
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in", extra_tags="success")
            return redirect("home")

        if (
            Semester.objects.get_current_semester() is None
            or not Semester.objects.get_current_semester().registration_open()
        ):
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
                "github_username": self.request.session.get("github_username") or "",
                "first_name": first_name,
                "last_name": last_name,
            }
        )

        return initial

    def form_valid(self, form):
        """Register new user if the form is valid."""
        try:
            user = self._register_user(form)
        except IntegrityError:
            messages.warning(self.request, "User already exists", extra_tags="danger")
            return redirect("home")
        finally:
            del self.request.session["github_id"]
            del self.request.session["github_username"]
            del self.request.session["github_name"]
            del self.request.session["github_email"]

        messages.success(self.request, "User created successfully", extra_tags="success")

        login(self.request, user, backend="github_oauth.backends.GithubOAuthBackend")

        return redirect("home")

    def _register_user(self, form):
        with transaction.atomic():
            github_id = self.request.session["github_id"]
            user = User.objects.create(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
            )

            user.groups.add(Role.objects.get(id=form.cleaned_data["course"]))
            user.save()

            GiphouseProfile.objects.create(
                user=user,
                github_username=self.request.session["github_username"],
                github_id=github_id,
                student_number=form.cleaned_data["student_number"],
            )

            Registration.objects.create(
                user=user,
                semester=Semester.objects.get_current_semester(),
                experience=form.cleaned_data["experience"],
                preference1=form.cleaned_data["project1"],
                preference2=form.cleaned_data["project2"],
                preference3=form.cleaned_data["project3"],
                comments=form.cleaned_data["comments"],
            )
        return user
