from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("admin/", admin.site.urls),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("oauth/", include("github_oauth.urls")),
    path("lectures/", include("courses.urls")),
    path("about/wayofworking", TemplateView.as_view(template_name="wayofworking.html"), name="wayofworking"),
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path("contact/", TemplateView.as_view(template_name="contact.html"), name="contact"),
    path("questionnaires/", include("questionnaires.urls")),
    path("register/", include("registrations.urls")),
    path("projects/", include("projects.urls")),
    path("reservations/", include("room_reservation.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
