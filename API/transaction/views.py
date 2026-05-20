from django.core.exceptions import ValidationError
from django.db import models
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Transaction
from .serializers import TransactionSerializer
from .services import (
    create_transaction,
    delete_transaction,
    transaction_payload,
    update_transaction,
)


def _route_user_matches(request, route_user):
    if route_user != request.user.username:
        return Response({"error": "Cannot access another user's transactions"}, status=status.HTTP_403_FORBIDDEN)
    return None


def _validation_response(exc):
    messages = getattr(exc, "messages", None)
    return Response(
        {"error": messages[0] if messages else str(exc)},
        status=status.HTTP_400_BAD_REQUEST,
    )


class TransactionCreate(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def post(self, request):
        try:
            item = create_transaction(request.user, request.data)
        except ValidationError as exc:
            return _validation_response(exc)
        except Exception as exc:
            return Response(
                {"error": "Failed to create transaction", "details": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = transaction_payload(item)
        response["status"] = "transaction saved"
        return Response(response, status=status.HTTP_201_CREATED)


class TransactionRetrieve(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get(self, request, user: str, account_id: str, month: int, year: int):
        mismatch = _route_user_matches(request, user)
        if mismatch:
            return mismatch

        base_query = Transaction.objects.filter(owner_user=request.user)

        if account_id != "0":
            base_query = base_query.filter(
                models.Q(account_fk_id=account_id)
                | models.Q(from_account_fk_id=account_id)
                | models.Q(to_account_fk_id=account_id)
            )

        if month != 0 and year != 0:
            base_query = base_query.filter(date__month=month, date__year=year)
        elif month != 0:
            base_query = base_query.filter(date__month=month)
        elif year != 0:
            base_query = base_query.filter(date__year=year)

        return Response([transaction_payload(item) for item in base_query.order_by("date", "id")])


class TransactionUpdate(generics.UpdateAPIView):
    serializer_class = TransactionSerializer

    def patch(self, request, transaction_id: str):
        try:
            item = update_transaction(request.user, transaction_id, request.data)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return _validation_response(exc)

        return Response(
            {"success": "Transaction updated successfully", "updated_transaction": transaction_payload(item)},
            status=status.HTTP_200_OK,
        )


class TransactionDelete(generics.DestroyAPIView):
    def delete(self, request, transaction_id: str):
        try:
            payload = delete_transaction(request.user, transaction_id)
        except Transaction.DoesNotExist:
            return Response({"error": "transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return _validation_response(exc)

        return Response({"status": "transaction deleted", "deleted_transaction": payload}, status=status.HTTP_200_OK)
