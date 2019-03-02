from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from courses.models import Lecture, Semester


class CoursesView(TemplateView):
    """View to display the lectures for a course."""

    template_name = 'courses.html'

    def get_context_data(self, **kwargs):
        """
        Overridden get_context_data method to add a list of courses and lectures to the template.

        :return: New context.
        """
        context = super(CoursesView, self).get_context_data(**kwargs)

        year = context.get('year')
        season = context.get('season')
        context['semester'] = get_object_or_404(Semester, year=year, semester=season)

        courses = {}
        for course_name, course_label in Lecture.COURSE_CHOICES:
            courses[course_label] = (
                Lecture
                .objects
                .filter(course=course_name, semester__year=year, semester__semester=season)
                .order_by(f'date')
            )

        context['courses'] = courses.items()
        return context
