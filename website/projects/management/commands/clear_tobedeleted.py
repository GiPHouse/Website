from django.core.management.base import BaseCommand

from projects.models import ProjectToBeDeleted, RepositoryToBeDeleted


class Command(BaseCommand):
    """Command to clear all objects to be deleted."""

    help = "Clear all objects to be deleted"

    def handle(self, *args, **options):
        """Clear all objects to be deleted."""
        RepositoryToBeDeleted.objects.all().delete()
        ProjectToBeDeleted.objects.all().delete()
