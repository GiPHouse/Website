from django.urls import path

from projects.views import ProjectsView

app_name = "projects"
urlpatterns = [path("<int:year>/<slug:season_slug>/", ProjectsView.as_view(), name="projects")]
