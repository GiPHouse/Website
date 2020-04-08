"""The services defined by the mailing lists package."""
from courses.models import Course, Semester

from registrations.models import Registration


def get_automatic_lists():
    """Return list of mailing lists that should be generated automatically."""
    current_semester = Semester.objects.get_or_create_current_semester()

    all_employees = Registration.objects.filter(semester=current_semester).select_related("user")

    se = Course.objects.se()
    sdm = Course.objects.sdm()

    all_engineers = Registration.objects.filter(course=se, semester=current_semester).select_related("user")
    all_managers = Registration.objects.filter(course=sdm, semester=current_semester).select_related("user")
    all_directors_emails = [
        reg.user.email
        for reg in Registration.objects.filter(semester=current_semester).select_related("user")
        if reg.is_director
    ]

    lists = [
        {
            "address": "employees",
            "aliases": [],
            "description": "Automatic moderated mailing list that can be used to send email to all employees",
            "addresses": all_employees.values_list("user__email", flat=True),
        },
        {
            "address": "engineers",
            "aliases": [],
            "description": "Automatic moderated mailing list that can be used to send email to all engineers",
            "addresses": all_engineers.values_list("user__email", flat=True),
        },
        {
            "address": "managers",
            "aliases": [],
            "description": "Automatic moderated mailing list that can be used to send email to all managers",
            "addresses": all_managers.values_list("user__email", flat=True),
        },
        {
            "address": "directors",
            "aliases": [],
            "description": "Automatic moderated mailing list that can be used to send email to all directors",
            "addresses": all_directors_emails,
        },
    ]

    return lists
