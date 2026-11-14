from django.db import models


class Task(models.Model):
    """A task."""

    total = models.IntegerField(null=True, blank=True, editable=False)
    completed = models.IntegerField(null=True, blank=True, editable=False)
    fail = models.BooleanField(default=False, editable=False)
    status = models.BooleanField(default=True)
    success_message = models.TextField(null=True, blank=True)
    data = models.TextField(null=True, blank=True, editable=False)
    redirect_url = models.CharField(max_length=60)
    logs = models.TextField(
        blank=True,
        default="",
        editable=False,
    )

    def __str__(self):
        """Show task as string."""
        return (
            f"Task with {self.completed} done out of {self.total} and "
            f"{'failed' if self.fail else ''} with redirect to {self.redirect_url}"
        )
