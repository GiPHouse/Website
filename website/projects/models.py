from django.db import models
from django.utils.text import slugify

from courses.models import Course, Semester

from registrations.models import Employee


class Client(models.Model):
    """Project client with logo."""

    class Meta:
        """Meta class for Client model."""

        ordering = ["name"]

    name = models.CharField(max_length=50, unique=True)

    logo = models.ImageField(upload_to="projects/images/", blank=True, null=True)

    def __str__(self):
        """Return client name."""
        return f"{self.name}"


class Project(models.Model):
    """Project group that contains multiple users."""

    class Meta:
        """Meta class for Project model."""

        ordering = ["semester", "name"]
        unique_together = [["name", "semester"]]

    name = models.CharField("name", max_length=50)

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    email = models.EmailField(blank=True)
    description = models.TextField()
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, blank=True, null=True)

    comments = models.TextField(
        null=True, blank=True, help_text="This is for private comments that are only available here."
    )

    def __str__(self):
        """Return project name and semester."""
        return f"{self.name} ({self.semester})"

    def save(self, *args, **kwargs):
        """Save project and add email if not set."""
        if not self.email:
            self.email = self.generate_email()
        super().save(*args, **kwargs)

    def generate_email(self):
        """Generate the standard email for this project."""
        return (
            f"{self.semester.year}"
            f"{self.semester.get_season_display().lower()}-"
            f"{slugify(self.name)}"
            f"@giphouse.nl"
        )

    def get_employees(self):
        """Query all employees assigned to this project."""
        return Employee.objects.filter(id__in=self.registration_set.values("user"))

    def get_engineers(self):
        """Query all engineers assigned to this project."""
        return Employee.objects.filter(
            id__in=self.registration_set.values("user"), registration__course=Course.objects.sde()
        )

    def get_managers(self):
        """Query all managers assigned to this project."""
        return Employee.objects.filter(
            id__in=self.registration_set.values("user"), registration__course=Course.objects.sdm()
        )
