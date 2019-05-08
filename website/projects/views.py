from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from courses.models import Semester

from projects.models import Project


class ProjectsView(TemplateView):
    """View to display the projects for a year."""

    template_name = 'projects/index.html'

    def get_context_data(self, year, season, **kwargs):
        """
        Overridden get_context_data method to add a list of projects to the template.

        :return: New context.
        """
        context = super(ProjectsView, self).get_context_data(**kwargs)

        context['projects_semester'] = get_object_or_404(Semester, year=year, season=season)
        context['projects'] = Project.objects.filter(semester__year=year, semester__season=season)
        return context
