from datetime import date, timedelta

from django.core.exceptions import ValidationError
from rest_framework import status
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


def validation_response(exc):
    messages = getattr(exc, "messages", None)
    return Response({"error": messages[0] if messages else str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringListCreate(APIView):
    def get(self, request):
        items = RecurringTransaction.objects.filter(owner_user=request.user).order_by("next_due_date", "id")
        return Response([recurring_payload(item) for item in items])

    def post(self, request):
        try:
            attrs = attrs_from_data(request.user, request.data)
            item = RecurringTransaction.objects.create(owner_user=request.user, **attrs)
        except (ValidationError, ValueError) as exc:
            return validation_response(exc)
        return Response(recurring_payload(item), status=status.HTTP_201_CREATED)


class RecurringDetail(APIView):
    def get_object(self, request, recurring_id):
        try:
            return RecurringTransaction.objects.get(owner_user=request.user, id=recurring_id)
        except RecurringTransaction.DoesNotExist:
            return None

    def get(self, request, recurring_id):
        item = self.get_object(request, recurring_id)
        if not item:
            return Response({"error": "Recurring transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(recurring_payload(item))

    def patch(self, request, recurring_id):
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

    def delete(self, request, recurring_id):
        item = self.get_object(request, recurring_id)
        if not item:
            return Response({"error": "Recurring transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response({"message": "Recurring transaction deleted successfully"})


class RecurringDue(APIView):
    def get(self, request):
        through = request.GET.get("through") or (date.today() + timedelta(days=3)).isoformat()
        try:
            items = generate_due_occurrences(request.user, through)
        except ValidationError as exc:
            return validation_response(exc)
        return Response([occurrence_payload(item) for item in items])


class RecurringPostDue(APIView):
    def post(self, request, occurrence_id):
        try:
            occurrence = post_occurrence(request.user, occurrence_id)
        except RecurringOccurrence.DoesNotExist:
            return Response({"error": "Recurring occurrence not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return validation_response(exc)
        return Response(occurrence_payload(occurrence))


class RecurringSkipDue(APIView):
    def post(self, request, occurrence_id):
        try:
            occurrence = skip_occurrence(request.user, occurrence_id)
        except RecurringOccurrence.DoesNotExist:
            return Response({"error": "Recurring occurrence not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return validation_response(exc)
        return Response(occurrence_payload(occurrence))
