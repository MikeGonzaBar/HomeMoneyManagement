from django.utils import timezone
from rest_framework import authentication, exceptions
from rest_framework.request import Request

from .models import AuthToken


class TokenAuthentication(authentication.BaseAuthentication):
    """Authenticate API requests using `Authorization: Token <key>`."""

    keyword = "Token"

    def authenticate_header(self, request: Request) -> str:
        """Return the header keyword expected by clients."""
        return self.keyword

    def authenticate(self, request: Request) -> tuple[object, AuthToken] | None:
        """Authenticate a request from an `Authorization: Token <key>` header."""
        auth_header = authentication.get_authorization_header(request).split()
        if not auth_header:
            return None

        if auth_header[0].decode().lower() != self.keyword.lower():
            return None

        if len(auth_header) != 2:
            raise exceptions.AuthenticationFailed("Invalid token header")

        try:
            key = auth_header[1].decode()
        except UnicodeError as exc:
            raise exceptions.AuthenticationFailed("Invalid token header") from exc

        try:
            token = AuthToken.objects.select_related("user").get(
                key=key,
                revoked_at__isnull=True,
            )
        except AuthToken.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Invalid or revoked token") from exc

        token.last_used_at = timezone.now()
        token.save(update_fields=["last_used_at"])
        return token.user, token
