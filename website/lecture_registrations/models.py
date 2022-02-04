from django.db import models

from courses.models import Lecture

from registrations.models import Employee


class LectureRegistration(models.Model):
    lecture = models.ForeignKey(Lecture, null=False, blank=False, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, null=True, blank=False, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Registration of {self.employee} for {self.lecture}"

    class Meta:
        verbose_name = "lecture registration"
