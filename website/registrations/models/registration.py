from difflib import SequenceMatcher

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.functional import cached_property

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

    ATTENDANCE_OFFLINE = 1
    ATTENDANCE_ONLINE = 2
    ATTENDANCE_PREFERRED_ONLINE = 3

    ATTENDANCE_CHOICES = (
        (ATTENDANCE_OFFLINE, "Attending offline"),
        (ATTENDANCE_ONLINE, "Only online"),
        (ATTENDANCE_PREFERRED_ONLINE, "Preferably online"),
    )

    class Meta:
        """Meta class for Registration."""

        unique_together = [["user", "semester"]]
        ordering = ["semester"]

    user = models.ForeignKey(Employee, on_delete=models.CASCADE)

    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    preference1 = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    preference2 = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    preference3 = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    partner_preference1 = models.CharField(null=True, blank=True, max_length=50)
    partner_preference2 = models.CharField(null=True, blank=True, max_length=50)
    partner_preference3 = models.CharField(null=True, blank=True, max_length=50)

    experience = models.PositiveSmallIntegerField(choices=EXPERIENCE_CHOICES)
    is_international = models.BooleanField(default=False)
    available_during_scheduled_timeslot = models.BooleanField(default=True)
    has_problems_with_signing_an_nda = models.BooleanField(default=False)
    attendance = models.PositiveSmallIntegerField(choices=ATTENDANCE_CHOICES, default=ATTENDANCE_OFFLINE)
    comments = models.TextField(null=True, blank=True)

    @property
    def is_director(self):
        """Check if a registration is a director."""
        return self.project is None and self.course == Course.objects.sdm()

    def _match_partner_name_to_user(self, name):
        """
        Match a string to a user.

        Find the most similar user name to the given name.
        """
        if name is None:
            return None

        ratios = {}
        for user in User.objects.filter(registration__semester=self.semester).all():
            ratio = SequenceMatcher(None, name, user.get_full_name()).ratio()
            if ratio > 0.5:
                ratios[user] = ratio

        if ratios:
            return max(ratios, key=lambda k: ratios[k])
        return None

    @cached_property
    def partner_preference1_user(self):
        """Get the user most similar to the first partner preference."""
        return self._match_partner_name_to_user(self.partner_preference1)

    @cached_property
    def partner_preference2_user(self):
        """Get the user most similar to the second partner preference."""
        return self._match_partner_name_to_user(self.partner_preference2)

    @cached_property
    def partner_preference3_user(self):
        """Get the user most similar to the third partner preference."""
        return self._match_partner_name_to_user(self.partner_preference3)

    def __str__(self):
        """Give user information about this object."""
        return f"{self.user.get_full_name()} ({self.semester})"
