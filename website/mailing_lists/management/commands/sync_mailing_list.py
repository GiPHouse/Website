from django.core.management.base import BaseCommand

from mailing_lists.gsuite import GSuiteSyncService


class Command(BaseCommand):
    """Command to run the mailing list sync."""

    help = "Run the GSuite sync"

    def handle(self, *args, **options):
        """Run mailing list sync."""
        sync = GSuiteSyncService()
        sync.sync_mailing_lists()
