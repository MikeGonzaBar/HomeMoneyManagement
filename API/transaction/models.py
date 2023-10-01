from django.db import models


class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    transaction_type = models.CharField(max_length=30)
    category = models.CharField(max_length=30)
    date = models.DateField(editable=True)
    title = models.CharField(max_length=120)
    total = models.FloatField(default=0.0)
    owner_id = models.CharField(max_length=20)
    account_id = models.CharField(max_length=20)

    @staticmethod
    def find_missing_data(data_dict: dict):
        keys_to_check = [
            "transaction_type",
            "category",
            "date",
            "title",
            "owner_id",
            "account_id",
            "total",
        ]
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
    def create_transaction(data: dict):
        missing_keys = Transaction.find_missing_data(data)

        if len(missing_keys) > 0:
            return {"error": "data incomplete", "missing_args": missing_keys}

        new_transaction = Transaction(
            transaction_type=data["transaction_type"],
            category=data["category"],
            date=data["date"],
            title=data["title"],
            owner_id=data["owner_id"],
            account_id=data["account_id"],
            total=data["total"],
        )
        new_transaction.save()

        query = Transaction.objects.filter(
            transaction_type=data["transaction_type"],
            category=data["category"],
            date=data["date"],
            title=data["title"],
            owner_id=data["owner_id"],
            account_id=data["account_id"],
            total=data["total"],
        )

        response = Transaction.queryset_to_array_of_dicts(query)
        response[0]["status"] = "transaction saved"
        return response[0]

    @staticmethod
    def get_transactions(user: str, account_id: str, month: int, year: int):
        base_query = Transaction.objects.filter(owner_id=user)

        if account_id != "0":
            base_query = base_query.filter(account_id=account_id)

        if month != 0 and year != 0:
            base_query = base_query.filter(date__month=month, date__year=year)
        elif month != 0:
            base_query = base_query.filter(date__month=month)
        elif year != 0:
            base_query = base_query.filter(date__year=year)

        return Transaction.queryset_to_array_of_dicts(base_query)

    @staticmethod
    def update_transactions(transaction_id: str, data: dict):
        try:
            transaction = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            return {"error": "Transaction not found"}

        # Update fields if present in the data dictionary, else use existing values
        transaction.transaction_type = data.get(
            "transaction_type", transaction.transaction_type
        )
        transaction.category = data.get("category", transaction.category)
        transaction.date = data.get("date", transaction.date)
        transaction.title = data.get("title", transaction.title)
        transaction.owner_id = data.get("owner_id", transaction.owner_id)
        transaction.account_id = data.get("account_id", transaction.account_id)
        transaction.total = data.get("total", transaction.total)

        transaction.save()
        return {
            "success": "Transaction updated successfully",
            "updated_transaction": transaction,
        }

    @staticmethod
    def delete_transaction(id: str):
        try:
            transaction = Transaction.objects.get(id=id)
        except Transaction.DoesNotExist:
            return {"error": "transaction not found"}
        transaction.delete()
        return {"status": "transaction deleted"}
