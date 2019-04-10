from courses.models import Semester
from peer_review.models import Questionnaire
from projects.models import Project


def add_menu_objects_to_context(request):
    """
    Context processor to add semesters to all requests.

    :param request: Request made by user.
    :return: All Semester objects
    """
    return {
        'current_semester': Semester.objects.first(),
        'current_projects': Project.objects.filter(semester=Semester.objects.first()),
        'semesters': Semester.objects.all(),
        'questionnaires': Questionnaire.objects.all() if request.user.is_authenticated else None,
    }
