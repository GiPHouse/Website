from django.http import HttpResponse
from django.shortcuts import render, get_list_or_404
from registrations.models import Project, Semester
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404


#def projectsview(request, year, semester):
#    projects variable is assigned a list of projects given by the year and semester parameters or returns a 404.
#    projects = get_list_or_404(Project.objects.filter(semester__year=year).filter(semester__semester=semester))
#    return render(request, "projects.html", context={'projects': projects})


class ProjectsView(TemplateView):
    template_name = 'projects.html'

    def get_context_data(self, **kwargs):
        """
        Overridden get_context_data method to add a list of projects to the template.
        :return: New context.
        """
        context = super(ProjectsView, self).get_context_data(**kwargs)
        year = context.get('year')
        season = context.get('season')
        context['projects'] = get_list_or_404(Project.objects.filter(semester__year=year).filter(semester__semester=season))
        return context
