from courses.models import Semester


def add_semesters_to_context(request):
    """
    Context processor to add semesters to all requests.

    :param request: Request made by user.
    :return: All Semester objects
    """
    return {
        'semesters': Semester.objects.all()
    }
