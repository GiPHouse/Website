from collections import defaultdict

from projects.models import Project

from django.views.generic import TemplateView


class OverviewView(TemplateView):
    template_name = "projects/index.html"

    def get_context_data(self, **kwargs):
        """
        Overridden get_context_data method to add a list of projects to the template.

        :return: New context.
        """
        context = super(OverviewView, self).get_context_data(**kwargs)

        # list is the type of the value here
        grouped = defaultdict(list)

        # select_related will load the needed classes right away,
        # no need to query for them when actually needing the data in the template
        for project in Project.objects.select_related("semester", "client"):
            grouped[project.semester.__str__()].append(project)

        context["grouped_projects"] = dict(grouped)

        return context
