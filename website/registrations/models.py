from enum import Enum

from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import Group

from courses.models import Semester

User = get_user_model()


class RoleChoice(Enum):
    se = "SE Student"
    sdm = "SDM Student"
    director = "Director"
    admin = "Admin"


class GiphouseProfile(models.Model):
    class Meta:
        verbose_name = "GiPHouse Profile"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    github_id = models.IntegerField(
        unique=True,
    )

    github_username = models.TextField(
        unique=True,
    )

    student_number = models.CharField(
        unique=True,
        null=True,
        max_length=8,
    )

    role = models.CharField(
        max_length=8,
        choices=[(tag.name, tag.value) for tag in RoleChoice],
    )

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'


class Project(Group):
    semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        null=True,
    )

    description = models.TextField()

    objects = models.Manager()

    def __str__(self):
        return f'{self.name} ({self.semester})'


class Registration(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    preference1 = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='+',
    )

    preference2 = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='+',
    )

    preference3 = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='+',
    )

    comments = models.TextField(
        null=True,
        blank=True,
    )

    def __str__(self):
        """Give basic information about this object"""
        return f'Registration for {self.user}'
