from django.core import validators
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from courses.models import Semester

from registrations.models import Employee


class AWSPolicy(models.Model):
    """AWS global base OU id, policy id and tags submission fields."""

    class Meta:
        """Meta class for AWSPolicy model."""

        verbose_name = "AWS Policy"
        verbose_name_plural = "AWS Policies"

    base_ou_id = models.CharField(max_length=50, unique=False, default="", null=False, blank=False)
    policy_id = models.CharField(max_length=50, unique=False, null=False, blank=False)
    tags_key = models.CharField(max_length=50, unique=False, default="", null=False, blank=False)
    tags_value = models.CharField(max_length=50, unique=False, default="", null=False, blank=True)
    is_current_policy = models.BooleanField(
        default=False,
        help_text="Attention: When saving this policy with 'is current policy' checked"
        + ", all other policies will be set to 'not current'!",
    )

    def save(self, *args, **kwargs):
        """Save method for AWSPolicy model."""
        if self.is_current_policy:
            AWSPolicy.objects.all().update(**{"is_current_policy": False})
        super(AWSPolicy, self).save(*args, **kwargs)

    def __str__(self):
        """Return policy id."""
        return f"{self.policy_id}"


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
        unique_together = [["name", "semester"], ["slug", "semester"]]

    name = models.CharField("name", max_length=50)
    slug = models.SlugField("slug", max_length=50, blank=False, null=False)

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    description = models.TextField()
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, blank=True, null=True)

    comments = models.TextField(
        null=True, blank=True, help_text="This is for private comments that are only available here."
    )

    github_team_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="This is the id of the team in the GitHub organization. ",
    )

    def __str__(self):
        """Return project name and semester."""
        return f"{self.name} ({self.semester})"

    def generate_email(self):
        """Generate the standard email for this project."""
        return f"{self.slug}-{self.semester.year}{self.semester.get_season_display().lower()}"

    def generate_team_description(self):
        """Generate the standardized team description for this project."""
        return f"Team for the GiPHouse project '{self.name}' for the '{self.semester}' semester."

    def get_employees(self):
        """Query all employees assigned to this project."""
        return Employee.objects.filter(id__in=self.registration_set.values("user"))

    @property
    def is_archived(self):
        """Check if a project is archived."""
        archived = self.repository_set.values_list("is_archived").order_by("is_archived")
        if archived:
            return archived.first()[0]
        else:
            return Repository.Archived.CONFIRMED

    @property
    def number_of_repos(self):
        """Return the number of repositories for a project."""
        return self.repository_set.count()


class ProjectToBeDeleted(models.Model):
    """Projects that are deleted in Django, but still need to be deleted on GitHub at the next sync."""

    github_team_id = models.IntegerField(
        null=False,
        blank=False,
        unique=True,
    )

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

    name = models.CharField("name", unique=True, max_length=55, validators=[validators.validate_slug])
    project = models.ForeignKey(Project, blank=True, null=True, on_delete=models.CASCADE)

    github_repo_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="This is the id of the GitHub repository.",
    )

    class Archived(models.IntegerChoices):
        """Archived state for repositories."""

        NOT_ARCHIVED = 0, "Not archived"
        PENDING = 1, "To be archived"
        CONFIRMED = 2, "Archived"

    is_archived = models.IntegerField(
        blank=False,
        null=False,
        choices=Archived.choices,
        default=Archived.NOT_ARCHIVED,
    )
    private = models.BooleanField(default=True)

    def __str__(self):
        """Return repository name."""
        return self.name


class RepositoryToBeDeleted(models.Model):
    """Repositories that are deleted in Django, but still need to be deleted on GitHub at the next sync."""

    github_repo_id = models.IntegerField(
        null=False,
        blank=False,
        unique=True,
    )

    def __str__(self):
        """Return id of repository to be deleted."""
        return f"Repository on GitHub with id {self.github_repo_id} to be deleted"

    @receiver(pre_delete, sender=Repository)
    def handle_repository_delete(instance, **kwargs):
        """Create a RepositoryToBeDeleted if a Repository is deleted."""
        if instance.github_repo_id is not None:
            RepositoryToBeDeleted.objects.create(github_repo_id=instance.github_repo_id)
