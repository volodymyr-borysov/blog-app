"""Django management command to clean up expired password reset tokens."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import PasswordResetToken


class Command(BaseCommand):
    """Delete expired password reset tokens from the database."""

    help = "Delete expired password reset tokens older than a specified number of days"

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete tokens expired more than this many days ago (default: 30)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        days = options["days"]
        dry_run = options["dry_run"]

        cutoff_date = timezone.now() - timedelta(days=days)

        # Find tokens to delete
        tokens_to_delete = PasswordResetToken.objects.filter(expires_at__lt=cutoff_date)
        count = tokens_to_delete.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No expired tokens found older than {days} days"
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would delete {count} expired token(s) older than {days} days"
                )
            )
            # Show some examples
            sample_tokens = tokens_to_delete[:5]
            self.stdout.write("\nExample tokens that would be deleted:")
            for token in sample_tokens:
                self.stdout.write(
                    f"  - {token.user.email}: expired on {token.expires_at}"
                )
            if count > 5:
                self.stdout.write(f"  ... and {count - 5} more")
        else:
            # Actually delete
            deleted_count, _ = tokens_to_delete.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {deleted_count} expired token(s) older than {days} days"
                )
            )
