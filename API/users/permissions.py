"""Custom DRF permissions for API-user authorization."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class IsApiAdmin(BasePermission):
    """Allow access only to authenticated users flagged for API admin mode."""

    message = "API admin access is required"

    def has_permission(self, request: Request, view: object) -> bool:
        """Return whether the authenticated token user has API admin privileges."""
        user = getattr(request, "user", None)
        return bool(getattr(user, "is_authenticated", False) and getattr(user, "is_admin", False))
