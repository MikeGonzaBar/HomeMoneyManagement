from decimal import Decimal, InvalidOperation

from django.db.models import ProtectedError
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Account
from .serializers import AccountSerializer


def _decimal_value(value, field_name, required=False):
    if value in (None, ""):
        if required:
            raise ValueError(f"{field_name} is required")
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid decimal number") from exc


def _account_payload(account):
    return {
        "id": account.id,
        "account_name": account.account_name,
        "account_type": account.account_type,
        "bank": account.bank,
        "total": float(account.total),
        "owner": account.owner,
        "credit_limit": float(account.credit_limit) if account.credit_limit is not None else None,
    }


def _route_user_matches(request, route_user):
    if route_user != request.user.username:
        return Response({"error": "Cannot access another user's accounts"}, status=status.HTTP_403_FORBIDDEN)
    return None


class AccountCreate(generics.CreateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def post(self, request):
        try:
            total = _decimal_value(request.data.get("total", 0), "total") or Decimal("0.00")
            credit_limit = _decimal_value(request.data.get("credit_limit"), "credit_limit")
            if credit_limit is not None and credit_limit < 0:
                raise ValueError("credit_limit must be greater than or equal to 0")

            account = Account.objects.create(
                account_name=request.data.get("account_name"),
                account_type=request.data.get("account_type"),
                bank=request.data.get("bank"),
                total=total,
                owner_user=request.user,
                credit_limit=credit_limit,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"error": "Failed to create account", "details": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = _account_payload(account)
        response["status"] = "Account saved"
        return Response(response, status=status.HTTP_201_CREATED)


class AccountOps(generics.RetrieveUpdateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def get(self, request, user: str, id: str):
        mismatch = _route_user_matches(request, user)
        if mismatch:
            return mismatch

        accounts = Account.objects.filter(owner_user=request.user).order_by("id")
        return Response([_account_payload(account) for account in accounts], status=status.HTTP_200_OK)

    def patch(self, request, user: str, id: str):
        mismatch = _route_user_matches(request, user)
        if mismatch:
            return mismatch

        try:
            account = Account.objects.get(owner_user=request.user, id=id)
        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        try:
            if "total" in data:
                data["total"] = _decimal_value(data.get("total"), "total", required=True)
            if "credit_limit" in data:
                data["credit_limit"] = _decimal_value(data.get("credit_limit"), "credit_limit")
                if data["credit_limit"] is not None and data["credit_limit"] < 0:
                    raise ValueError("credit_limit must be greater than or equal to 0")
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        is_credit_card = account.is_credit_card
        old_credit_limit = account.credit_limit
        new_credit_limit = data.get("credit_limit")
        if is_credit_card and old_credit_limit and new_credit_limit and old_credit_limit != new_credit_limit:
            used_credit = old_credit_limit - account.total
            data["total"] = max(Decimal("0.00"), new_credit_limit - used_credit)

        allowed_fields = {"account_name", "account_type", "bank", "total", "credit_limit"}
        for key, value in data.items():
            if key in allowed_fields:
                setattr(account, key, value)
        account.owner_user = request.user
        account.save()

        return Response(
            {"success": "Account updated successfully", "updated_account": _account_payload(account)},
            status=status.HTTP_200_OK,
        )


class AccountDelete(generics.DestroyAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def delete(self, request, user: str, id: str):
        mismatch = _route_user_matches(request, user)
        if mismatch:
            return mismatch

        try:
            account = Account.objects.get(owner_user=request.user, id=id)
        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            account.delete()
        except ProtectedError:
            return Response(
                {"error": "Account cannot be deleted while transactions reference it"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"success": "Account deleted successfully"}, status=status.HTTP_200_OK)
