from enum import Enum

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class RoleChoice(Enum):
    se = "SE Student"
    sdm = "SDM Student"
    director = "Director"
    admin = "Admin"


class SeasonChoice(Enum):
    fall = "Fall"
    spring = "Spring"


class GiPHouseProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    github_id = models.IntegerField(
        unique=True,
    )

    github_username = models.TextField(
        unique=True,
    )

    snumber = models.IntegerField(
        unique=True,
        null=True,
    )

    role = models.CharField(
        max_length=8,
        choices=[(tag, tag.value) for tag in RoleChoice]
    )


class Semester(models.Model):
    year = models.IntegerField()
    semester = models.CharField(
        max_length=5,
        choices=[(tag, tag.value) for tag in SeasonChoice]
    )


class Project(models.Model):
    name = models.TextField()

    academic_year = models.ForeignKey(
        Semester,
        on_delete=models.DO_NOTHING
    )

    description = models.TextField()

    members = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING
    )
