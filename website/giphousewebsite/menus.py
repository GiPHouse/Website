"""
This file defines the menu layout.

We set the variable `:py:main` to form the menu tree.
"""
from courses.models import Semester

from django.urls import reverse

from peer_review.models import Questionnaire

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
        'title': 'Peer Review',
        'visible': lambda request: (Questionnaire.objects.open_questionnaires().count() > 1
                                    and request.user.is_authenticated),
        'url': reverse('peer_review:overview')
    },
    {
        'title': 'Peer Review',
        'visible': lambda request: (Questionnaire.objects.open_questionnaires().count() == 1 and
                                    request.user.is_authenticated),
        'url': lambda: (reverse('peer_review:answer', args=(Questionnaire.objects.first().pk,))
                        if Questionnaire.objects.first() else False)
    }
]
