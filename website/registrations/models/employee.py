from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class EmployeeManager(BaseUserManager):
    """Manager for Employee class."""

    def _create_user(self, github_id, **extra_fields):
        """Create user given the fields."""
        user = self.model(github_id=github_id, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, github_id, **extra_fields):
        """Create standard user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(github_id, **extra_fields)

    def create_superuser(self, github_id, **extra_fields):
        """Create superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("first_name", "Super")
        extra_fields.setdefault("last_name", "User")
        return self._create_user(github_id, **extra_fields)


class Employee(AbstractUser):
    """Employee of GiPHouse."""

    USERNAME_FIELD = "github_id"
    REQUIRED_FIELDS = ["github_username"]

    username = None
    github_id = models.IntegerField(unique=True)
    github_username = models.CharField(unique=True, max_length=50)

    student_number = models.CharField(unique=True, null=True, max_length=8)

    objects = EmployeeManager()

    def __str__(self):
        """Return the full name for this student."""
        if self.student_number:
            return f"{self.get_full_name()} ({self.student_number})"
        return f"{self.get_full_name()}"
