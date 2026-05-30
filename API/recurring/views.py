from datetime import date, timedelta

from django.core.exceptions import ValidationError
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RecurringOccurrence, RecurringTransaction
from .services import (
    attrs_from_data,
    generate_due_occurrences,
    occurrence_payload,
    post_occurrence,
    recurring_payload,
    skip_occurrence,
)


class RecurringSchemaSerializer(serializers.Serializer):
    """Named schema placeholder for hand-built recurring API responses."""


def validation_response(exc: ValidationError) -> Response:
    """Convert validation exceptions into the API error shape."""
    messages = getattr(exc, "messages", None)
    return Response({"error": messages[0] if messages else str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringListCreate(generics.GenericAPIView):
    """List and create recurring transaction rules for the token user."""

    serializer_class = RecurringSchemaSerializer

    @extend_schema(
        tags=["Recurring"],
        operation_id="recurring_transaction_list",
        responses={200: OpenApiResponse(description="Recurring transaction rules")},
    )
    def get(self, request: Request) -> Response:
        """Return active and inactive recurring rules for the token user."""
        items = RecurringTransaction.objects.filter(owner_user=request.user).order_by("next_due_date", "id")
        return Response([recurring_payload(item) for item in items])

    @extend_schema(
        tags=["Recurring"],
        operation_id="recurring_transaction_create",
        responses={201: OpenApiResponse(description="Recurring rule created")},
    )
    def post(self, request: Request) -> Response:
        """Create a recurring transaction rule for the token user."""
        try:
            attrs = attrs_from_data(request.user, request.data)
            item = RecurringTransaction.objects.create(owner_user=request.user, **attrs)
        except (ValidationError, ValueError) as exc:
            return validation_response(exc)
        return Response(recurring_payload(item), status=status.HTTP_201_CREATED)


class RecurringDetail(generics.GenericAPIView):
    """Retrieve, update, or delete one recurring transaction rule."""

    serializer_class = RecurringSchemaSerializer

    def get_object(self, request: Request, recurring_id: int) -> RecurringTransaction | None:
        """Return one owned recurring rule or None."""
        try:
            return RecurringTransaction.objects.get(owner_user=request.user, id=recurring_id)
        except RecurringTransaction.DoesNotExist:
            return None

    @extend_schema(
        tags=["Recurring"],
        operation_id="recurring_transaction_retrieve",
        responses={200: OpenApiResponse(description="Recurring rule details")},
    )
    def get(self, request: Request, recurring_id: int) -> Response:
        """Return one recurring rule owned by the token user."""
        item = self.get_object(request, recurring_id)
        if not item:
            return Response({"error": "Recurring transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(recurring_payload(item))

    @extend_schema(
        tags=["Recurring"],
        operation_id="recurring_transaction_update",
        responses={200: OpenApiResponse(description="Recurring rule updated")},
    )
    def patch(self, request: Request, recurring_id: int) -> Response:
        """Update one recurring rule owned by the token user."""
        item = self.get_object(request, recurring_id)
        if not item:
            return Response({"error": "Recurring transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            attrs = attrs_from_data(request.user, request.data, existing=item)
            for key, value in attrs.items():
                setattr(item, key, value)
            item.save()
        except (ValidationError, ValueError) as exc:
            return validation_response(exc)
        return Response(recurring_payload(item))

    @extend_schema(
        tags=["Recurring"],
        operation_id="recurring_transaction_delete",
        responses={200: OpenApiResponse(description="Recurring rule deleted")},
    )
    def delete(self, request: Request, recurring_id: int) -> Response:
        """Delete one recurring rule owned by the token user."""
        item = self.get_object(request, recurring_id)
        if not item:
            return Response({"error": "Recurring transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response({"message": "Recurring transaction deleted successfully"})


class RecurringDue(APIView):
    """Generate and list due recurring occurrences."""

    @extend_schema(
        tags=["Recurring"],
        operation_id="recurring_occurrence_due_list",
        parameters=[OpenApiParameter("through", str, OpenApiParameter.QUERY)],
        responses={200: OpenApiResponse(description="Due recurring occurrences")},
    )
    def get(self, request: Request) -> Response:
        """Return due occurrences through a date query parameter."""
        through = request.GET.get("through") or (date.today() + timedelta(days=3)).isoformat()
        try:
            items = generate_due_occurrences(request.user, through)
        except ValidationError as exc:
            return validation_response(exc)
        return Response([occurrence_payload(item) for item in items])


class RecurringPostDue(APIView):
    """Post a due recurring occurrence."""

    @extend_schema(
        tags=["Recurring"],
        operation_id="recurring_occurrence_post",
        request=None,
        responses={200: OpenApiResponse(description="Occurrence posted")},
    )
    def post(self, request: Request, occurrence_id: int) -> Response:
        """Create a transaction from a due occurrence."""
        try:
            occurrence = post_occurrence(request.user, occurrence_id)
        except RecurringOccurrence.DoesNotExist:
            return Response({"error": "Recurring occurrence not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return validation_response(exc)
        return Response(occurrence_payload(occurrence))


class RecurringSkipDue(APIView):
    """Skip a due recurring occurrence."""

    @extend_schema(
        tags=["Recurring"],
        operation_id="recurring_occurrence_skip",
        request=None,
        responses={200: OpenApiResponse(description="Occurrence skipped")},
    )
    def post(self, request: Request, occurrence_id: int) -> Response:
        """Mark an occurrence skipped without creating a transaction."""
        try:
            occurrence = skip_occurrence(request.user, occurrence_id)
        except RecurringOccurrence.DoesNotExist:
            return Response({"error": "Recurring occurrence not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return validation_response(exc)
        return Response(occurrence_payload(occurrence))
