import json
from django.http import HttpRequest, HttpResponse
from rest_framework import generics
from .models import Account
from .serializers import AccountSerializer


# Create your views here.
class AccountCreate(generics.CreateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def post(self, request: HttpRequest) -> HttpResponse:
        data = json.loads(request.body)
        try:
            # Create account directly
            account = Account.objects.create(
                account_name=data.get('account_name'),
                account_type=data.get('account_type'),
                bank=data.get('bank'),
                total=data.get('total', 0.0),
                owner=data.get('owner')
            )
            response = {
                "id": account.id,
                "account_name": account.account_name,
                "account_type": account.account_type,
                "bank": account.bank,
                "total": account.total,
                "owner": account.owner,
                "status": "Account saved"
            }
            status = 201
        except Exception as e:
            response = {"error": "Failed to create account", "details": str(e)}
            status = 400
        
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )


class AccountOps(generics.RetrieveUpdateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def get(self, request: HttpRequest, user: str, id: str) -> HttpResponse:
        try:
            # Get accounts for user
            accounts = Account.objects.filter(owner=user)
            response = []
            for account in accounts:
                response.append({
                    "id": account.id,
                    "account_name": account.account_name,
                    "account_type": account.account_type,
                    "bank": account.bank,
                    "total": account.total,
                    "owner": account.owner
                })
        except Exception as e:
            response = {"error": "Failed to get accounts", "details": str(e)}
        
        return HttpResponse(
            json.dumps(response, default=str),
            status=200,
            content_type="application/json",
        )

    def patch(self, request: HttpRequest, user: str, id: str) -> HttpResponse:
        data = json.loads(request.body)
        try:
            account = Account.objects.get(owner=user, id=id)
            for key, value in data.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            account.save()
            response = {
                "success": "Account updated successfully",
                "updated_account": {
                    "id": account.id,
                    "account_name": account.account_name,
                    "account_type": account.account_type,
                    "bank": account.bank,
                    "total": account.total,
                    "owner": account.owner
                }
            }
        except Account.DoesNotExist:
            response = {"error": "Account not found"}
        except Exception as e:
            response = {"error": "Failed to update account", "details": str(e)}
        
        return HttpResponse(
            json.dumps(response, default=str),
            status=200,
            content_type="application/json",
        )


class AccountDelete(generics.DestroyAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def delete(self, request: HttpRequest, user: str, id: str) -> HttpResponse:
        try:
            account = Account.objects.get(owner=user, id=id)
            account.delete()
            response = {"success": "Account deleted successfully"}
            status = 200
        except Account.DoesNotExist:
            response = {"error": "Account not found"}
            status = 400
        except Exception as e:
            response = {"error": "Failed to delete account", "details": str(e)}
            status = 400
        
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )
