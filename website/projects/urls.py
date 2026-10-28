from django.urls import path

from projects.views import OverviewView

app_name = "projects"
urlpatterns = [
    path("", OverviewView.as_view(), name="overview"),
]
