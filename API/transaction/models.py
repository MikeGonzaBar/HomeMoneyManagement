from typing import Optional
from django.db import models


class Transaction(models.Model):
    """
    Represents a transaction in the system.

    Attributes:
        id (int): The ID of the transaction.
        transaction_type (str): The type of the transaction.
        category (str): The category of the transaction.
        date (DateField): The date of the transaction.
        title (str): The title of the transaction.
        total (float): The total amount of the transaction.
        owner_id (str): The ID of the owner of the transaction.
        account_id (str): The ID of the account associated with the transaction.

    Methods:
        find_missing_data(data_dict: dict) -> list: Finds missing or empty values in the provided data dictionary.
        queryset_to_array_of_dicts(queryset: models.query.QuerySet, fields: Optional[list[str]] = None) -> list[dict]: Converts a Django QuerySet to an array of dictionaries.
        create_transaction(data: dict) -> dict: Creates a transaction based on the provided data.
        get_transactions(user: str, account_id: str, month: int, year: int) -> list[dict]: Retrieves transactions based on the specified user, account, month, and year.
        update_transactions(transaction_id: str, data: dict) -> dict: Updates a transaction with the provided data.
        delete_transaction(id: str) -> dict: Deletes a transaction with the specified ID.
    """

    id = models.AutoField(primary_key=True)
    transaction_type = models.CharField(max_length=30)
    category = models.CharField(max_length=30)
    date = models.DateField(editable=True)
    title = models.CharField(max_length=120)
    total = models.FloatField(default=0.0)
    owner_id = models.CharField(max_length=20)
    account_id = models.CharField(max_length=20)

    @staticmethod
    def find_missing_data(data_dict: dict) -> list:
        """
        Finds missing or empty values in the provided data dictionary.

        Args:
            data_dict (dict): A dictionary of data to check for missing or empty values.

        Returns:
            list: A list of keys that are missing or have empty values.

        Example:
            ```python
            data = {
                "transaction_type": "expense",
                "category": "",
                "date": "2022-01-01",
                "title": "Groceries",
                "owner_id": 123,
                "account_id": "",
                "total": 50.0
            }

            missing_keys = Transaction.find_missing_data(data)
            print(missing_keys)
            ```
        """
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
    def queryset_to_array_of_dicts(
        queryset: models.query.QuerySet, fields: Optional[list[str]] = None
    ) -> list[dict]:
        """
            Converts a Django QuerySet to an array of dictionaries.

            Args:
                queryset (models.query.QuerySet): The Django QuerySet to convert.
                fields (Optional[list[str]]): A list of fields to include in the resulting dictionaries. If not provided, all fields will be included.

            Returns:
                list[dict]: An array of dictionaries representing the objects in the QuerySet.

            Example:
                ```python
                queryset = Transaction.objects.all()
                fields = ["transaction_type", "category", "date"]
                result = Transaction.queryset_to_array_of_dicts(queryset, fields)
                print(result)
                ```
        """

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
    def create_transaction(data: dict) -> dict:
        """
        Creates a transaction based on the provided data.

        Args:
            data (dict): A dictionary containing the data for the transaction.

        Returns:
            dict: A dictionary representing the created transaction.

        Raises:
            None

        Example:
            ```python
            data = {
                "transaction_type": "expense",
                "category": "food",
                "date": "2022-01-01",
                "title": "Groceries",
                "owner_id": 123,
                "account_id": 456,
                "total": 50.0
            }

            transaction = Transaction.create_transaction(data)
            print(transaction)
            ```
        """
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
    def get_transactions(user: str, account_id: str, month: int, year: int)->list[dict]:
        """
        Retrieves transactions based on the provided filters.

        Args:
            user (str): The ID of the user.
            account_id (str): The ID of the account. Use "0" to retrieve transactions from all accounts.
            month (int): The month of the transactions. Use 0 to retrieve transactions from all months.
            year (int): The year of the transactions. Use 0 to retrieve transactions from all years.

        Returns:
            list[dict]: A list of dictionaries representing the retrieved transactions.

        Example:
            ```python
            user_id = "12345"
            account_id = "9876"
            month = 2
            year = 2022
            transactions = Transaction.get_transactions(user_id, account_id, month, year)
            print(transactions)
            ```
        """
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
    def update_transactions(transaction_id: str, data: dict)->dict:
        """
        Updates a transaction with the specified ID using the provided data.

        Args:
            transaction_id (str): The ID of the transaction to update.
            data (dict): A dictionary containing the updated data for the transaction.

        Returns:
            dict: A dictionary indicating the status of the update and the updated transaction.

        Example:
            ```python
            transaction_id = "12345"
            data = {
                "transaction_type": "income",
                "category": "salary",
                "date": "2022-02-01",
                "title": "Monthly Salary",
                "owner_id": "9876",
                "account_id": "6543",
                "total": 5000.0
            }
            result = Transaction.update_transactions(transaction_id, data)
            print(result)
            ```
        """

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
    def delete_transaction(id: str)->dict:
        """
        Deletes a transaction with the specified ID.

        Args:
            id (str): The ID of the transaction to delete.

        Returns:
            dict: A dictionary indicating the status of the deletion.

        Example:
            ```python
            transaction_id = "12345"
            result = Transaction.delete_transaction(transaction_id)
            print(result)
            ```
        """

        try:
            transaction = Transaction.objects.get(id=id)
        except Transaction.DoesNotExist:
            return {"error": "transaction not found"}
        transaction.delete()
        return {"status": "transaction deleted"}
