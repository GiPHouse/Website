from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.models import User as DjangoUser
from django.db import models

from courses.models import Semester

from projects.models import Project

User: DjangoUser = get_user_model()

User.__str__ = lambda x: x.get_full_name()

SDM = "SDM Student"
SE = "SE Student"


class Role(Group):
    """Role Group that contains multiple users."""

    objects = models.Manager()

    def __str__(self):
        """Return role name."""
        return f'{self.name}'


class GiphouseProfile(models.Model):
    """Model with GiPHouse specific data."""

    class Meta:
        """Meta class specifying name of model."""

        verbose_name = "GiPHouse Profile"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Save the giphouseprofile and insert the username in the related user object.

        This overrides the default implementation of save to be able to change the model before inserting. After the
        change, the default save() method is still called
        """
        self.user.username = 'github_' + str(self.github_id)
        self.user.save()
        super().save(force_insert, force_update, using, update_fields)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    github_id = models.IntegerField(
        unique=True,
    )

    github_username = models.CharField(
        unique=True,
        max_length=50,
    )

    student_number = models.CharField(
        unique=True,
        null=True,
        max_length=8,
    )

    def __str__(self):
        """Return full name of user."""
        return f'{self.user.get_full_name()}'


class Registration(models.Model):
    """Model containing registration specific data."""

    unique_together = [['user', 'semester']]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    semester = models.ForeignKey(
        Semester,
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
        """Give user information about this object."""
        return f'{self.user.giphouseprofile}'
