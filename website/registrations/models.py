from enum import Enum

from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import Group

User = get_user_model()


class RoleChoice(Enum):
    se = "SE Student"
    sdm = "SDM Student"
    director = "Director"
    admin = "Admin"


class SeasonChoice(Enum):
    fall = "Fall"
    spring = "Spring"

    def __str__(self):
        return self.value


class Semester(models.Model):
    year = models.IntegerField()
    semester = models.CharField(
        max_length=6,
        choices=[(tag.name, tag.value) for tag in SeasonChoice]
    )

    def __str__(self):
        return f'{SeasonChoice[self.semester]} {self.year}'


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

    snumber = models.IntegerField(
        unique=True,
        null=True
    )

    role = models.CharField(
        max_length=8,
        choices=[(tag.name, tag.value) for tag in RoleChoice]
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
