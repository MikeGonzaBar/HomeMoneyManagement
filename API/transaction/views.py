import json
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from rest_framework import generics
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionCreate(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def post(self, request: HttpRequest) -> HttpResponse:
        data = json.loads(request.body)
        response = Transaction.create_transaction(data)
        status = 400 if "error" in response else 201
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )


class TransactionRetrieve(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get(
        self, request: HttpRequest, user: str, account_id: str, month: int, year: int
    ) -> HttpResponse:
        response = Transaction.get_transactions(user, account_id, month, year)
        return HttpResponse(
            json.dumps(response, default=str),
            status=200,
            content_type="application/json",
        )


class TransactionUpdate(generics.UpdateAPIView):
    def patch(self, request: HttpRequest, transaction_id: str) -> HttpResponse:
        data = json.loads(request.body)
        response = Transaction.update_transactions(transaction_id, data)
        return HttpResponse(
            json.dumps(response, default=str),
            status=200,
            content_type="application/json",
        )


class TransactionDelete(generics.DestroyAPIView):
    def delete(self, request, transaction_id: str) -> HttpResponse:
        response = Transaction.delete_transaction(transaction_id)
        status = 400 if "error" in response else 200
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )
