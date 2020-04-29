from django.core.management.base import BaseCommand

from projects.githubsync import GitHubSync
from projects.models import Project


class Command(BaseCommand):
    """Command to run the GitHub sync."""

    help = "Synchronise teams and repositories to GitHub"

    def handle(self, *args, **options):
        """Run GitHub sync."""
        sync = GitHubSync(Project.objects.all())
        sync.perform_sync()
