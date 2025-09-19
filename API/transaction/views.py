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
        try:
            # Create transaction directly
            transaction = Transaction.objects.create(
                transaction_type=data.get('transaction_type'),
                category=data.get('category'),
                date=data.get('date'),
                title=data.get('title'),
                total=data.get('total', 0.0),
                owner_id=data.get('owner_id'),
                account_id=data.get('account_id')
            )
            response = {
                "id": transaction.id,
                "transaction_type": transaction.transaction_type,
                "category": transaction.category,
                "date": transaction.date,
                "title": transaction.title,
                "total": transaction.total,
                "owner_id": transaction.owner_id,
                "account_id": transaction.account_id,
                "status": "transaction saved"
            }
            status = 201
        except Exception as e:
            response = {"error": "Failed to create transaction", "details": str(e)}
            status = 400
        
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
        try:
            # Get transactions with filters
            base_query = Transaction.objects.filter(owner_id=user)
            
            if account_id != "0":
                base_query = base_query.filter(account_id=account_id)
            
            if month != 0 and year != 0:
                base_query = base_query.filter(date__month=month, date__year=year)
            elif month != 0:
                base_query = base_query.filter(date__month=month)
            elif year != 0:
                base_query = base_query.filter(date__year=year)
            
            response = []
            for transaction in base_query:
                response.append({
                    "id": transaction.id,
                    "transaction_type": transaction.transaction_type,
                    "category": transaction.category,
                    "date": transaction.date,
                    "title": transaction.title,
                    "total": transaction.total,
                    "owner_id": transaction.owner_id,
                    "account_id": transaction.account_id
                })
        except Exception as e:
            response = {"error": "Failed to get transactions", "details": str(e)}
        
        return HttpResponse(
            json.dumps(response, default=str),
            status=200,
            content_type="application/json",
        )


class TransactionUpdate(generics.UpdateAPIView):
    def patch(self, request: HttpRequest, transaction_id: str) -> HttpResponse:
        data = json.loads(request.body)
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            for key, value in data.items():
                if hasattr(transaction, key):
                    setattr(transaction, key, value)
            transaction.save()
            response = {
                "success": "Transaction updated successfully",
                "updated_transaction": {
                    "id": transaction.id,
                    "transaction_type": transaction.transaction_type,
                    "category": transaction.category,
                    "date": transaction.date,
                    "title": transaction.title,
                    "total": transaction.total,
                    "owner_id": transaction.owner_id,
                    "account_id": transaction.account_id
                }
            }
        except Transaction.DoesNotExist:
            response = {"error": "Transaction not found"}
        except Exception as e:
            response = {"error": "Failed to update transaction", "details": str(e)}
        
        return HttpResponse(
            json.dumps(response, default=str),
            status=200,
            content_type="application/json",
        )


class TransactionDelete(generics.DestroyAPIView):
    def delete(self, request, transaction_id: str) -> HttpResponse:
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            transaction.delete()
            response = {"status": "transaction deleted"}
            status = 200
        except Transaction.DoesNotExist:
            response = {"error": "transaction not found"}
            status = 400
        except Exception as e:
            response = {"error": "Failed to delete transaction", "details": str(e)}
            status = 400
        
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )
