from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from typing import Any

from .models import AuthToken, User
from .serializers import UserLoginSerializer, UserResponseSerializer, UserSerializer
from .services import UserService


def _user_payload(user: User) -> dict[str, object]:
    """Build the public authenticated user payload returned by auth endpoints."""
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "theme_preference": user.theme_preference,
        "is_admin": user.is_admin,
    }


def _auth_payload(user: User, token: AuthToken) -> dict[str, object]:
    """Build the token response returned after registration or login."""
    return {
        "valid": True,
        "token": token.key,
        "user": _user_payload(user),
    }


class UserRegistrationView(generics.CreateAPIView):
    """Register a finance app user and issue an API token."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=UserSerializer,
        responses={
            201: inline_serializer(
                name="AuthTokenResponse",
                fields={
                    "valid": serializers.BooleanField(),
                    "token": serializers.CharField(),
                    "user": UserResponseSerializer(),
                },
            ),
            400: OpenApiResponse(description="Invalid registration data"),
        },
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Validate registration data, create a user, and return a token."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"valid": False, "error": "Invalid registration data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        token = AuthToken.issue_for_user(user)
        return Response(_auth_payload(user, token), status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """Authenticate a finance app user and issue an API token."""

    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: inline_serializer(
                name="LoginTokenResponse",
                fields={
                    "valid": serializers.BooleanField(),
                    "token": serializers.CharField(),
                    "user": UserResponseSerializer(),
                },
            ),
            400: OpenApiResponse(description="Invalid login data"),
            401: OpenApiResponse(description="Invalid credentials"),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Authenticate username/password credentials and issue a token."""
        username_from_url = kwargs.get("username")
        if username_from_url:
            username_or_email = username_from_url
            password = request.data.get("password")
            if not password:
                return Response(
                    {"valid": False, "error": "Password is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"valid": False, "error": "Invalid login data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            username_or_email = serializer.validated_data["username_or_email"]
            password = serializer.validated_data["password"]

        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            return Response(
                {"valid": False, "error": "User not found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"valid": False, "error": "Incorrect password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = AuthToken.issue_for_user(user)
        return Response(_auth_payload(user, token), status=status.HTTP_200_OK)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Authenticated user detail operations."""

    queryset = User.objects.all()
    serializer_class = UserResponseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "username"

    def get_object(self) -> User:
        """Return only the route user when it matches the authenticated user."""
        user = super().get_object()
        if user.id != self.request.user.id:
            self.permission_denied(self.request, message="Cannot access another user")
        return user

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Return the authenticated user's detail payload."""
        return Response({"user": _user_payload(self.get_object())}, status=status.HTTP_200_OK)

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete the authenticated user after password confirmation."""
        user = self.get_object()
        password = request.data.get("password")
        if not password:
            return Response(
                {"error": "Password required for account deletion"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.check_password(password):
            return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
        result = UserService.delete_user(user.username, password)
        if result.get("success"):
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    responses={
        200: inline_serializer(
            name="UserProfileResponse",
            fields={"user": UserResponseSerializer()},
        )
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request: Request) -> Response:
    """Return the authenticated user's profile."""
    return Response({"user": _user_payload(request.user)}, status=status.HTTP_200_OK)


@extend_schema(
    request=inline_serializer(
        name="UpdateUserInfoRequest",
        fields={
            "new_username": serializers.CharField(required=False),
            "first_name": serializers.CharField(required=False),
            "last_name": serializers.CharField(required=False),
        },
    ),
    responses={200: OpenApiResponse(description="User information updated")},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_info(request: Request) -> Response:
    """Update the authenticated user's username and display name."""

    user = request.user
    new_username = request.data.get("new_username", user.username)
    first_name = request.data.get("first_name", user.first_name)
    last_name = request.data.get("last_name", user.last_name)

    if not new_username:
        return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)

    if new_username != user.username and User.objects.filter(username=new_username).exists():
        return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    old_username = user.username
    user.username = new_username
    user.first_name = first_name
    user.last_name = last_name
    user.save()

    if old_username != new_username:
        from account.models import Account
        from bankstatements.models import BankStatement
        from transaction.models import Transaction

        Account.objects.filter(owner_user=user).update(owner=new_username)
        Transaction.objects.filter(owner_user=user).update(owner_id=new_username)
        BankStatement.objects.filter(owner_user=user).update(user_id=new_username)

    return Response({"message": "User information updated successfully", "user": _user_payload(user)})


@extend_schema(
    request=inline_serializer(
        name="ChangePasswordRequest",
        fields={
            "current_password": serializers.CharField(),
            "new_password": serializers.CharField(),
        },
    ),
    responses={200: OpenApiResponse(description="Password changed")},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def change_password(request: Request) -> Response:
    """Change the authenticated user's password after current-password verification."""

    user = request.user
    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")

    if not current_password or not new_password:
        return Response(
            {"error": "Missing required fields", "message": "Please provide current_password and new_password"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.check_password(current_password):
        return Response(
            {"error": "Invalid current password", "message": "The current password you entered is incorrect"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password(new_password)
    except DjangoValidationError as exc:
        return Response(
            {"error": "Invalid new password", "details": list(exc.messages)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.save()
    AuthToken.objects.filter(user=user, revoked_at__isnull=True).exclude(
        key=getattr(request.auth, "key", None)
    ).update(revoked_at=timezone.now())
    return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)


@extend_schema(
    request=inline_serializer(
        name="UserPreferencesRequest",
        fields={"theme_preference": serializers.ChoiceField(choices=("system", "light", "dark"))},
    ),
    responses={200: OpenApiResponse(description="User preferences")},
)
@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def user_preferences(request: Request) -> Response:
    """Read or update authenticated user preferences."""

    user = request.user
    if request.method == "GET":
        return Response({"theme_preference": user.theme_preference, "user": _user_payload(user)})

    theme = request.data.get("theme_preference", user.theme_preference)
    if theme not in {"system", "light", "dark"}:
        return Response(
            {"error": "theme_preference must be system, light, or dark"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user.theme_preference = theme
    user.save(update_fields=["theme_preference"])
    return Response(
        {
            "message": "Preferences updated successfully",
            "theme_preference": theme,
            "user": _user_payload(user),
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(request=None, responses={200: OpenApiResponse(description="Token revoked")})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request: Request) -> Response:
    """Revoke the current API token."""

    if request.auth:
        request.auth.revoked_at = timezone.now()
        request.auth.save(update_fields=["revoked_at"])
    return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
