from django.core.management.base import BaseCommand

from projects import githubsync
from projects.models import Project, Repository


class Command(BaseCommand):
    """Command to clear a GitHub organization fully."""

    help = "Remove all teams and repositories from organization"

    def handle(self, *args, **options):
        """Remove all teams and repositories from organization."""
        message = (
            "THIS WILL DELETE ALL REPOSITORIES FROM THE ORGANIZATION (NOT ARCHIVE). THIS CANNOT BE UNDONE. ARE "
            "YOU SURE YOU WANT TO PROCEED? "
        )
        confirmed = input(f"{message} (y/N)\n").lower() == "y"
        if confirmed:
            message = "ARE YOU ABSOLUTELY SURE? "
            confirmed2 = input(f"{message} (y/N)\n").lower() == "y"
            if confirmed2:
                githubsync.talker.remove_all_teams_from_organization()
                githubsync.talker.delete_all_repositories_from_organization()
                Repository.objects.update(github_repo_id=None)
                Project.objects.update(github_team_id=None)
