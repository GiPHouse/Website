from django.contrib.auth.models import Group
from django.db import models
from django.utils.text import slugify

from courses.models import Semester


class Client(models.Model):
    """Project client with logo."""

    name = models.CharField(
        max_length=50,
    )

    logo = models.ImageField(
        upload_to='projects/images/',
        blank=True,
        null=True,
    )

    def __str__(self):
        """Return client name."""
        return f'{self.name}'


class Project(Group):
    """Project group that contains multiple users."""

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
    )

    email = models.EmailField(blank=True)

    description = models.TextField()

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    objects = models.Manager()

    def __str__(self):
        """Return project name and semester."""
        return f'{self.name} ({self.semester})'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """Save project and add email if not set."""
        if not self.email:
            self.email = self.generate_email()
        super().save(force_insert, force_update, using, update_fields)

    def generate_email(self):
        """Generate the standard email for this project."""
        return (f'{self.semester.year}'
                f'{self.semester.get_season_display().lower()}-'
                f'{slugify(self.name)}'
                f'@giphouse.nl')
