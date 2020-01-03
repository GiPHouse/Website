import os

from courses.models import Semester

from projects.models import Project


def source_commit(request):
    """Get the COMMIT_HASH environment variable."""
    return {"COMMIT_HASH": os.environ.get("COMMIT_HASH", "unknown")}


def add_menu_objects_to_context(request):
    """
    Context processor to add semesters to all requests.

    :param request: Request made by user.
    :return: All Semester objects
    """
    return {
        "current_semester": Semester.objects.get_or_create_current_semester(),
        "current_projects": Project.objects.filter(semester=Semester.objects.get_or_create_current_semester()),
    }
