from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class Account(models.Model):
    id = models.AutoField(primary_key=True)
    account_type = models.CharField(max_length=30)
    bank = models.CharField(max_length=30)
    total = models.FloatField(default=0.0)
    account_name = models.CharField(max_length=30)
    owner = models.CharField(max_length=150)

    @staticmethod
    def find_missing_data(data_dict: dict):
        keys_to_check = ["account_type", "bank", "total", "owner", "account_name"]
        return [
            key for key in keys_to_check if key not in data_dict or not data_dict[key]
        ]

    @staticmethod
    def queryset_to_array_of_dicts(queryset: models.query.QuerySet, fields=None):
        result_array = []
        model_fields = [f.name for f in queryset.model._meta.get_fields()]
        for obj in queryset:
            obj_dict = {
                field: getattr(obj, field)
                for field in fields or model_fields
                if field in model_fields
            }
            result_array.append(obj_dict)
        return result_array

    @staticmethod
    def create_account(data: dict):
        missing_keys = Account.find_missing_data(data)

        if len(missing_keys) > 0:
            return {"error": "data incomplete", "missing_args": missing_keys}

        new_account = Account(
            account_type=data["account_type"],
            bank=data["bank"],
            total=data["total"],
            owner=data["owner"],
            account_name=data["account_name"],
        )
        new_account.save()

        query = Account.objects.filter(
            account_type=data["account_type"],
            bank=data["bank"],
            total=data["total"],
            owner=data["owner"],
            account_name=data["account_name"],
        )

        response = Account.queryset_to_array_of_dicts(query)
        response[0]["status"] = "Account saved"
        return response[0]

    @staticmethod
    def get_accounts(user: str):
        query = Account.objects.filter(owner=user)
        return Account.queryset_to_array_of_dicts(query)

    @staticmethod
    def update_account(user, data: dict):
        owner = user
        account_name = data.get("account_name")
        bank = data.get("bank")
        account_type = data.get("account_type")
        new_total = data.get("total")

        try:
            account = Account.objects.get(
                owner=owner,
                account_name=account_name,
                bank=bank,
                account_type=account_type,
            )
        except Account.DoesNotExist:
            return {"error": "Account not found"}

        account.total = new_total
        account.save()

        return {"success": "Account updated successfully", "updated_account": account}

    @staticmethod
    def delete_account(user, id):
        try:
            account = Account.objects.get(
                owner=user,
                id=id,
            )
        except ObjectDoesNotExist:
            return {"error": "Account not found"}

        account.delete()

        return {"success": "Account deleted successfully"}
