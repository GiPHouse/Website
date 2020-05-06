from django.core import validators
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
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
    description = models.TextField()
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, blank=True, null=True)

    comments = models.TextField(
        null=True, blank=True, help_text="This is for private comments that are only available here."
    )

    github_team_id = models.IntegerField(
        null=True, blank=True, unique=True, help_text="This is the id of the team in the GitHub organization. ",
    )

    def __str__(self):
        """Return project name and semester."""
        return f"{self.name} ({self.semester})"

    def generate_email(self):
        """Generate the standard email for this project."""
        return f"{self.semester.year}{self.semester.get_season_display().lower()}-{slugify(self.name)}"

    def generate_team_description(self):
        """Generate the standardized team description for this project."""
        return f"Team for the GiPHouse project '{self.name}' for the '{self.semester}' semester."

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

    @property
    def is_archived(self):
        """Check if a project is archived."""
        return not self.repository_set.filter(is_archived=False).exists()


class ProjectToBeDeleted(models.Model):
    """Projects that are deleted in Django, but still need to be deleted on GitHub at the next sync."""

    github_team_id = models.IntegerField(null=False, blank=False, unique=True,)

    def __str__(self):
        """Return id of team to be deleted."""
        return f"Team on GitHub with id {self.github_team_id} to be deleted"

    @receiver(pre_delete, sender=Project)
    def handle_project_delete(instance, **kwargs):
        """Create a ProjectToBeDeleted if a Project is deleted and delete all it's repositories."""
        if instance.github_team_id is not None:
            ProjectToBeDeleted.objects.create(github_team_id=instance.github_team_id)


class Repository(models.Model):
    """GitHub repository for a project team. Teams can have multiple repositories."""

    class Meta:
        """Meta class for Repository."""

        verbose_name_plural = "Repositories"

    name = models.CharField("name", unique=True, max_length=50, validators=[validators.validate_slug])
    project = models.ForeignKey(Project, blank=True, null=True, on_delete=models.CASCADE)

    github_repo_id = models.IntegerField(
        null=True, blank=True, unique=True, help_text="This is the id of the GitHub repository.",
    )

    is_archived = models.BooleanField(
        blank=False,
        null=False,
        default=False,
        help_text="This is the 'archived' value of the GitHub repository. Archived repositories will be set to"
        "archived on GitHub, meaning they are read only. Reverting the archived value of a repository will have to be "
        "done manually in GitHub, if the un-archiving a repository is desired.",
    )

    private = models.BooleanField(default=True)

    def __str__(self):
        """Return repository name."""
        return self.name


class RepositoryToBeDeleted(models.Model):
    """Repositories that are deleted in Django, but still need to be deleted on GitHub at the next sync."""

    github_repo_id = models.IntegerField(null=False, blank=False, unique=True,)

    def __str__(self):
        """Return id of repository to be deleted."""
        return f"Repository on GitHub with id {self.github_repo_id} to be deleted"

    @receiver(pre_delete, sender=Repository)
    def handle_repository_delete(instance, **kwargs):
        """Create a RepositoryToBeDeleted if a Repository is deleted."""
        if instance.github_repo_id is not None:
            RepositoryToBeDeleted.objects.create(github_repo_id=instance.github_repo_id)
