"""Admin-mode API endpoints for managing token-auth users."""

from django.db.models import Count, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuthToken, User
from .permissions import IsApiAdmin
from .serializers import AdminUserSerializer, AdminUserUpdateSerializer


def _admin_user_queryset() -> QuerySet[User]:
    """Return users annotated with active token counts for admin responses."""
    return User.objects.annotate(
        active_token_count=Count(
            "auth_tokens",
            filter=Q(auth_tokens__revoked_at__isnull=True),
        )
    ).order_by("id")


class AdminUserList(APIView):
    """List API users for authenticated API admins."""

    permission_classes = [IsApiAdmin]

    @extend_schema(
        tags=["API Admin"],
        responses={200: AdminUserSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        """Return all API users without passwords or token values."""
        users = _admin_user_queryset()
        return Response(AdminUserSerializer(users, many=True).data, status=status.HTTP_200_OK)


class AdminUserDetail(APIView):
    """Update safe API-user fields for authenticated API admins."""

    permission_classes = [IsApiAdmin]

    @extend_schema(
        tags=["API Admin"],
        request=AdminUserUpdateSerializer,
        responses={
            200: inline_serializer(
                name="AdminUserUpdateResponse",
                fields={"user": AdminUserSerializer()},
            ),
            400: OpenApiResponse(description="Invalid user update"),
            404: OpenApiResponse(description="User not found"),
        },
    )
    def patch(self, request: Request, user_id: int) -> Response:
        """Apply a partial update to a safe subset of API-user fields."""
        user = get_object_or_404(User, id=user_id)
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("is_admin") is False:
            other_admin_exists = User.objects.filter(is_admin=True).exclude(id=user.id).exists()
            if not other_admin_exists:
                return Response(
                    {"error": "At least one API admin user must remain"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer.save()
        updated_user = _admin_user_queryset().get(id=user.id)
        return Response({"user": AdminUserSerializer(updated_user).data}, status=status.HTTP_200_OK)


class AdminUserTokenRevoke(APIView):
    """Revoke active API tokens for a selected API user."""

    permission_classes = [IsApiAdmin]

    @extend_schema(
        tags=["API Admin"],
        request=None,
        responses={
            200: inline_serializer(
                name="AdminTokenRevokeResponse",
                fields={"revoked_tokens": serializers.IntegerField()},
            ),
            404: OpenApiResponse(description="User not found"),
        },
    )
    def post(self, request: Request, user_id: int) -> Response:
        """Revoke every currently active token for the target API user."""
        user = get_object_or_404(User, id=user_id)
        revoked_tokens = AuthToken.objects.filter(user=user, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )
        return Response({"revoked_tokens": revoked_tokens}, status=status.HTTP_200_OK)
