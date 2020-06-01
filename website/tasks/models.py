from django.db import models


class Task(models.Model):
    """A task."""

    total = models.IntegerField(null=True, blank=True)
    completed = models.IntegerField(null=True, blank=True)
    fail = models.BooleanField(default=False)
    success_message = models.TextField(null=True, blank=True)
    data = models.TextField(null=True, blank=True)
    redirect_url = models.CharField(max_length=60)

    def __str__(self):
        """Show task as string."""
        return (
            f"Task with {self.completed} done out of {self.total} and "
            f"{'failed' if self.fail else ''} with redirect to {self.redirect_url}"
        )
