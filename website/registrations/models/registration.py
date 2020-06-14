from django.contrib.auth import get_user_model
from django.db import models

from fuzzyset import FuzzySet

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
    comments = models.TextField(null=True, blank=True)

    @property
    def is_director(self):
        """Check if a registration is a director."""
        return self.project is None and self.course == Course.objects.sdm()

    @staticmethod
    def _match_partner_name_to_user(name, semester):
        """Match a string to a user."""
        if name:
            user_names = FuzzySet()
            users = {}
            for user in User.objects.filter(registration__semester=semester).all():
                user_names.add(user.get_full_name())
                users[user.get_full_name()] = user
            matches = user_names.get(name)
            if matches:
                best_match = sorted(user_names.get(name))[0]
                return users[best_match[1]] if best_match[0] > 0.50 else None
        return None

    @property
    def partner_preference1_user(self):
        """Get the user most similar to the first partner preference."""
        return self._match_partner_name_to_user(self.partner_preference1, self.semester)

    @property
    def partner_preference2_user(self):
        """Get the user most similar to the second partner preference."""
        return self._match_partner_name_to_user(self.partner_preference2, self.semester)

    @property
    def partner_preference3_user(self):
        """Get the user most similar to the third partner preference."""
        return self._match_partner_name_to_user(self.partner_preference3, self.semester)

    def get_preferred_partners(self):
        """Get the preferred project partners of a user."""
        return User.objects.filter(
            pk__in=[
                self.partner_preference1_user.pk,
                self.partner_preference2_user.pk,
                self.partner_preference3_user.pk,
            ]
        ).distinct()

    def get_partner1_display(self):
        """Get the displayable version for a registration's 1st preferred project partner."""
        if self.partner_preference1_user:
            return self.partner_preference1_user
        elif self.partner_preference1:
            return f"'{self.partner_preference1}'"
        return None

    def get_partner2_display(self):
        """Get the displayable version for a registration's 2nd preferred project partner."""
        if self.partner_preference2_user:
            return self.partner_preference2_user
        elif self.partner_preference2:
            return f"'{self.partner_preference2}'"
        return None

    def get_partner3_display(self):
        """Get the displayable version for a registration's 3rd preferred project partner."""
        if self.partner_preference3_user:
            return self.partner_preference3_user
        elif self.partner_preference3:
            return f"'{self.partner_preference3}'"
        return None

    def __str__(self):
        """Give user information about this object."""
        return f"{self.user.get_full_name()} ({self.semester})"
