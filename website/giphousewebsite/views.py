from django.shortcuts import get_list_or_404
from registrations.models import Project
from django.views.generic import TemplateView


class ProjectsView(TemplateView):
    """View to display the projects for a year."""

    template_name = 'projects.html'

    def get_context_data(self, year, season, **kwargs):
        """
        Overridden get_context_data method to add a list of projects to the template.

        :return: New context.
        """
        context = super(ProjectsView, self).get_context_data(**kwargs)
        context['projects'] = get_list_or_404(
            Project.objects.filter(semester__year=year).filter(semester__season=season))
        return context
