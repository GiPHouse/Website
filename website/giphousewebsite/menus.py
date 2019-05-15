"""
This file defines the menu layout.

We set the variable `:py:main` to form the menu tree.
"""
from django.urls import reverse

from courses.models import Semester


__all__ = ['MAIN_MENU']

"""
Defines the menu layout as a nested dict

The authenticated key indicates something should only
be visible for logged-in users. *Do not* rely on that for authentication!
"""
MAIN_MENU = [
    {'title': 'Home', 'url': reverse('home')},
    {
        'title': 'About',
        'submenu': [
            {'title': 'About GiPHouse', 'url': reverse('about')},
            {'title': 'Way of working', 'url': reverse('wayofworking')},
        ],
    },
    {
        'title': 'Course Content',
        'submenu': lambda: [{'title': str(semester), 'url': reverse('courses:lectures',
                                                                    args=(semester.year, semester.season))}
                            for semester in Semester.objects.all()],
    },
    {
        'title': 'Projects',
        'submenu': lambda: [{'title': str(semester), 'url': reverse('projects:projects',
                                                                    args=(semester.year, semester.season))}
                            for semester in Semester.objects.all()],
    },
    {
        'title': 'Contact',
        'url': reverse('contact'),
    },
    {
        'title': 'Room Reservation',
        'url': reverse('room_reservation:calendar'),
        'visible': lambda request: request.user.is_authenticated,
    },
    {
        'title': 'Questionnaires',
        'visible': lambda request: request.user.is_authenticated,
        'url': reverse('questionnaires:overview')
    },

]
