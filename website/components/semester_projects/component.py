from django_components import component


@component.register("semester_projects")
class SemesterProjects(component.Component):
    template_name = "semester_projects/template.html"

    def get_context_data(self, semester, projects):
        return {
            "semester": semester,
            "projects": projects,
        }

    class Media:
        css = ["semester_projects/style.css"]
        js = ["semester_projects/script.js"]
