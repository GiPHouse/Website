from django.db import models
from django.contrib.auth.models import User


class GiPHouseProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    github_id = models.IntegerField(
        unique=True
    )
