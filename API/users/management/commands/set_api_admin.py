"""Promote or demote a token-auth API user for admin-mode endpoints."""

from django.core.management.base import BaseCommand, CommandParser

from users.models import User


class Command(BaseCommand):
    """Set the API admin flag on an existing users.User record."""

    help = "Promote or demote a token-auth API user for /api-admin/ endpoints."

    def add_arguments(self, parser: CommandParser) -> None:
        """Register command-line arguments."""
        parser.add_argument("username", help="API username to update.")
        parser.add_argument(
            "--enabled",
            choices=("true", "false"),
            default="true",
            help="Whether the user should have API admin privileges.",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Apply the requested API admin flag."""
        username = str(options["username"])
        enabled = str(options["enabled"]).lower() == "true"
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'API user "{username}" does not exist.'))
            return

        if not enabled and not User.objects.filter(is_admin=True).exclude(id=user.id).exists():
            self.stderr.write(self.style.ERROR("At least one API admin user must remain."))
            return

        user.is_admin = enabled
        user.save(update_fields=["is_admin"])
        state = "enabled" if enabled else "disabled"
        self.stdout.write(self.style.SUCCESS(f'API admin mode {state} for "{username}".'))
