from django.urls import path
from django.views.generic import RedirectView

from registrations.views import Step1View, Step2View

app_name = "registrations"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="registrations:step1")),
    path("step1", Step1View.as_view(), name="step1"),
    path("step2", Step2View.as_view(), name="step2"),
]
