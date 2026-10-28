from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """AppConfig for projects app."""

    name = "projects"
    label = "projects"

    import components.semester_projects.component
