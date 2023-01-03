from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView, TemplateView

from github_oauth.templatetags.github_tags import url_github_callback


class GitHubLoginRedirectView(RedirectView):
    """Redirect to GitHub login page."""

    permanent = True
    query_string = True
    pattern_name = "login-redirect"

    def get_redirect_url(self, *args, **kwargs):
        """Return the redirect url for GitHub login."""
        return url_github_callback(
            {"request": self.request}, "login", next_url=reverse_lazy("admin:index")
        )  # pragma: no cover


urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("admin/login/", GitHubLoginRedirectView.as_view(), name="login-redirect"),
    path("admin/logout/", RedirectView.as_view(url="/logout", query_string=True), name="logout-redirect"),
    path("admin/", admin.site.urls),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("oauth/", include("github_oauth.urls")),
    path("lectures/", include("courses.urls")),
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path("for-companies/", TemplateView.as_view(template_name="for-companies.html"), name="for-companies"),
    path("contact/", TemplateView.as_view(template_name="contact.html"), name="contact"),
    path("questionnaires/", include("questionnaires.urls")),
    path("register/", include("registrations.urls")),
    path("projects/", include("projects.urls")),
    path("reservations/", include("room_reservation.urls")),
    path("lectures/", include("lecture_registrations.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
