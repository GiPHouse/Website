from django.db import models

from courses.models import Lecture

from registrations.models import Employee


class LectureRegistration(models.Model):
    """Registrations for lectures."""

    lecture = models.ForeignKey(Lecture, null=False, blank=False, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, null=True, blank=False, on_delete=models.SET_NULL)

    def __str__(self):
        """Return string representation of lecture registration."""
        return f"Registration of {self.employee} for {self.lecture}"

    class Meta:
        """Metaclass for lecture registrations."""

        verbose_name = "lecture registration"
