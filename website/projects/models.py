from django.contrib.auth.models import Group
from django.db import models

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
