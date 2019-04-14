from enum import Enum

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.db import models

from projects.models import Project

User: DjangoUser = get_user_model()


def users_in_same_group(user: User):
    """Return the queryset of users from the groups that the user is in."""
    return User.objects.filter(groups__in=user.groups.all()).exclude(pk=user.pk)


class RoleChoice(Enum):
    """Possible roles."""

    se = "SE Student"
    sdm = "SDM Student"
    director = "Director"
    admin = "Admin"


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
        """Return full name of user."""
        return f'{self.user.first_name} {self.user.last_name}'


class Registration(models.Model):
    """Model containing registration specific data."""

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
        """Give user information about this object."""
        return f'{self.user.giphouseprofile}'
