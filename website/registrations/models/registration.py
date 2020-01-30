from django.contrib.auth import get_user_model
from django.db import models

from courses.models import Course, Semester

from projects.models import Project

from registrations.models import Employee

User: Employee = get_user_model()


class Registration(models.Model):
    """Model containing registration specific data."""

    EXPERIENCE_BEGINNER = 1
    EXPERIENCE_INTERMEDIATE = 2
    EXPERIENCE_ADVANCED = 3

    EXPERIENCE_CHOICES = (
        (EXPERIENCE_BEGINNER, "Beginner"),
        (EXPERIENCE_INTERMEDIATE, "Intermediate"),
        (EXPERIENCE_ADVANCED, "Advanced"),
    )

    class Meta:
        """Meta class for Registration."""

        unique_together = [["user", "semester"]]
        ordering = ["semester"]

    user = models.ForeignKey(Employee, on_delete=models.CASCADE)

    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    preference1 = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="+")
    preference2 = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    preference3 = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="+")

    experience = models.PositiveSmallIntegerField(choices=EXPERIENCE_CHOICES)
    education_background = models.TextField(max_length=200)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        """Give user information about this object."""
        return f"{self.user.get_full_name()} ({self.semester})"
