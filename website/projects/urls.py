from django.urls import path

from projects.views import ProjectsView

app_name = 'projects'
urlpatterns = [
    path('<int:year>/<slug:season>/', ProjectsView.as_view(), name='projects'),
]
