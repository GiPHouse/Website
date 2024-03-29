from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.http.response import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import Resolver404, resolve, reverse_lazy
from django.views import View

from courses.models import Semester

from github_oauth.backends import GithubOAuthBackend, GithubOAuthError

from registrations.models import Employee

User: Employee = get_user_model()


class BaseGithubView(View):
    """Base View for Github OAuth."""

    redirect_url_success = settings.LOGIN_REDIRECT_URL
    redirect_url_failure = settings.LOGIN_REDIRECT_URL

    def get(self, request, code):
        """Handle GET request made by Github OAuth."""
        return redirect(self._get_redirect_url(request))

    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and if the code GET parameter exists."""
        if request.method != "GET":
            return self.http_method_not_allowed(request)

        try:
            code = request.GET["code"]
        except KeyError:
            return HttpResponseBadRequest()

        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in", extra_tags="success")
            return redirect(self._get_redirect_url(request))

        return self.get(request, code)

    @staticmethod
    def _get_redirect_url(request, default_url=redirect_url_success):
        """
        Return the path to redirect to.

        If the 'next' parameter is present and resolves to a known view, use it.
        Otherwise return the 'default_url'.
        """
        try:
            redirect_path = request.GET["next"]
            resolve(redirect_path)
            return redirect_path
        except (Resolver404, KeyError):
            return default_url


class GithubLoginView(BaseGithubView):
    """View accessed by GitHub after an authorization request of a user trying to login."""

    def get(self, request, code):
        """Handle GET request made by Github OAuth."""
        user = authenticate(request, code=code)

        if user is not None:
            login(request, user)
            messages.success(request, "Login Successful", extra_tags="success")
            return redirect(self._get_redirect_url(request, default_url=self.redirect_url_failure))
        elif Semester.objects.get_first_semester_with_open_registration():  # pragma: no cover
            messages.warning(request, "Redirecting to course registration", extra_tags="danger")
            return redirect(reverse_lazy("registrations:step1"))

        messages.warning(request, "Login Failed", extra_tags="danger")
        return redirect(self._get_redirect_url(request, default_url=self.redirect_url_failure))


class GithubRegisterView(BaseGithubView):
    """View accessed by GitHub after an authorization request of a user trying to register."""

    redirect_url_success = reverse_lazy("registrations:step2")

    def get(self, request, code):
        """Handle GET request made by Github OAuth."""
        backend = GithubOAuthBackend()

        try:
            github_info = backend.get_github_info(code)
        except GithubOAuthError as error_message:
            messages.warning(request, str(error_message), extra_tags="danger")
            return redirect(self._get_redirect_url(request, default_url=self.redirect_url_failure))

        try:
            user = User.objects.get(
                github_id=github_info["id"], registration__semester=Semester.objects.get_or_create_current_semester()
            )
        except User.DoesNotExist:
            pass
        else:
            login(request, user, backend="github_oauth.backends.GithubOAuthBackend")
            messages.success(request, "You already have an account.", extra_tags="success")
            return redirect(self._get_redirect_url(request, default_url=self.redirect_url_failure))

        request.session.update(
            {
                "github_id": github_info["id"],
                "github_username": github_info["login"],
                "github_email": github_info["email"],
                "github_name": github_info["name"],
            }
        )

        return redirect(self.redirect_url_success)
