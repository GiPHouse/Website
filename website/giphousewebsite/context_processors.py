from courses.models import Semester
from peer_review.models import Questionnaire


def add_menu_objects_to_context(request):
    """
    Context processor to add semesters to all requests.

    :param request: Request made by user.
    :return: All Semester objects
    """
    if request.user.is_authenticated:
        questionnaires = Questionnaire.objects.all()
    else:
        questionnaires = None

    return {
        'semesters': Semester.objects.all(),
        'questionnaires': questionnaires,
    }
