from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from courses.models import Course, Lecture, Semester


class CoursesView(TemplateView):
    """View to display the lectures for a course."""

    template_name = "courses/index.html"

    def get_context_data(self, **kwargs):
        """
        Overridden get_context_data method to add a list of courses and lectures to the template.

        :return: New context.
        """
        context = super(CoursesView, self).get_context_data(**kwargs)

        context["lecture_semester"] = get_object_or_404(
            Semester, year=self.kwargs["year"], season=Semester.slug_to_season(self.kwargs["season_slug"])
        )

        courses = {}
        for course_name in Course.objects.values_list("name", flat=True):
            courses[course_name] = Lecture.objects.filter(
                course__name=course_name,
                semester__year=self.kwargs["year"],
                semester__season=Semester.slug_to_season(self.kwargs["season_slug"]),
            ).order_by("date")

        context["courses"] = courses.items()
        return context
