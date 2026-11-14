from django_components import component


@component.register("project_card")
class ProjectCard(component.Component):
    template_name = "project_card/template.html"

    def get_context_data(self, project):
        return {
            "project": project,
        }
