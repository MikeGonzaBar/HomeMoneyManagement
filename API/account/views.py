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
                owner=data.get('owner'),
                credit_limit=data.get('credit_limit', None)
            )
            response = {
                "id": account.id,
                "account_name": account.account_name,
                "account_type": account.account_type,
                "bank": account.bank,
                "total": account.total,
                "owner": account.owner,
                "credit_limit": account.credit_limit,
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
                    "owner": account.owner,
                    "credit_limit": account.credit_limit
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
            
            # For credit cards, if credit_limit is being changed, recalculate available credit
            # to preserve the used credit amount
            is_credit_card = account.account_type in ['Crédito', 'Credit Card', 'Credit']
            old_credit_limit = account.credit_limit
            new_credit_limit = data.get('credit_limit')
            
            if is_credit_card and old_credit_limit and new_credit_limit and old_credit_limit != new_credit_limit:
                # Calculate used credit before the change
                used_credit = old_credit_limit - account.total
                # Recalculate available credit with new limit
                new_available_credit = new_credit_limit - used_credit
                # Update total to reflect new available credit
                data['total'] = max(0, new_available_credit)  # Ensure non-negative
            
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
                    "owner": account.owner,
                    "credit_limit": account.credit_limit
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
