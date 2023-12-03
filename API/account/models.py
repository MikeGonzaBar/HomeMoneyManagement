from typing import Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class Account(models.Model):
    """
    Represents an account in the system.

    Attributes:
        id (int): The ID of the account.
        account_type (str): The type of the account.
        bank (str): The bank associated with the account.
        total (float): The total amount in the account.
        account_name (str): The name of the account.
        owner (str): The owner of the account.

    Methods:
        find_missing_data(data_dict: dict) -> list: Finds missing data keys in the provided data dictionary.
        queryset_to_array_of_dicts(queryset: models.query.QuerySet, fields: Optional[list[str]] = None) -> list[dict]: Converts a Django queryset to an array of dictionaries.
        create_account(data: dict) -> dict: Creates an account based on the provided data.
        get_accounts(user: str) -> list[dict]: Retrieves the accounts belonging to the specified user.
        update_account(user: str, data: dict) -> dict: Updates an account with the provided data for the specified user.
        delete_account(user: str, id: int) -> dict: Deletes an account with the specified ID for the given user.
    """

    id = models.AutoField(primary_key=True)
    account_type = models.CharField(max_length=30)
    bank = models.CharField(max_length=30)
    total = models.FloatField(default=0.0)
    account_name = models.CharField(max_length=30)
    owner = models.CharField(max_length=150)

    @staticmethod
    def find_missing_data(data_dict: dict) -> list:
        """
        Finds missing data keys in the provided data dictionary.

        Args:
            data_dict (dict): A dictionary containing the data to check for missing keys.

        Returns:
            list: A list of missing keys in the data dictionary.

        Raises:
            None

        Example:
            ```python
            data = {
                "account_type": "savings",
                "bank": "ABC Bank",
                "total": 1000.0,
                "owner": "John Doe"
            }

            missing_keys = Transaction.find_missing_data(data)
            print(missing_keys)
            ```
        """
        keys_to_check = ["account_type", "bank", "total", "owner", "account_name"]
        return [
            key
            for key in keys_to_check
            if key not in data_dict or data_dict[key] is None
        ]

    @staticmethod
    def queryset_to_array_of_dicts(
        queryset: models.query.QuerySet, fields: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Converts a Django queryset to an array of dictionaries.

        Args:
            queryset (models.query.QuerySet): The Django queryset to convert.
            fields (Optional[list[str]]): Optional list of fields to include in the dictionaries. If not provided, all fields of the model will be included. Default is None.

        Returns:
            list[dict]: An array of dictionaries representing the queryset.

        Raises:
            None

        Example:
            ```python
            queryset = Transaction.objects.filter(category="food")
            fields = ["title", "date", "total"]

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
    def create_account(data: dict) -> dict:
        """
        Creates an account based on the provided data.

        Args:
            data (dict): A dictionary containing the data for the account.

        Returns:
            dict: A dictionary representing the created account.

        Raises:
            None

        Example:
            ```python
            data = {
                "account_type": "savings",
                "bank": "ABC Bank",
                "total": 1000.0,
                "owner": "John Doe",
                "account_name": "My Savings Account"
            }

            account = Account.create_account(data)
            print(account)
            ```
        """
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
    def get_accounts(user: str) -> list[dict]:
        """
        Retrieves the accounts belonging to the specified user.

        Args:
            user (str): The username of the user.

        Returns:
            list[dict]: A list of dictionaries representing the user's accounts.

        Raises:
            None

        Example:
            ```python
            user = "JohnDoe"

            accounts = Account.get_accounts(user)
            print(accounts)
            ```
        """

        query = Account.objects.filter(owner=user)
        return Account.queryset_to_array_of_dicts(query)

    @staticmethod
    def update_account(user: str, id: str, data: dict) -> dict:
        """
        Updates an account with the provided data for the specified user.

        Args:
            user (str): The username of the user.
            id (str): The ID of the account to update.
            data (dict): A dictionary containing the updated data for the account.

        Returns:
            dict: A dictionary representing the updated account.

        Raises:
            None

        Example:
            ```python
            user = "JohnDoe"
            id = "123"
            data = {
                "account_name": "My Savings Account",
                "bank": "ABC Bank",
                "account_type": "savings",
                "total": 1500.0
            }

            updated_account = Account.update_account(user, id, data)
            print(updated_account)
            ```
        """

        owner = user

        try:
            account = Account.objects.get(
                owner=owner,
                id=id,
            )
        except Account.DoesNotExist:
            return {"error": "Account not found"}

        for key, value in data.items():
            setattr(account, key, value)

        account.save()

        return {"success": "Account updated successfully", "updated_account": account}

    @staticmethod
    def delete_account(user: str, id: int) -> dict:
        """
        Deletes an account with the specified ID for the given user.

        Args:
            user (str): The username of the user.
            id (int): The ID of the account to delete.

        Returns:
            dict: A dictionary indicating the success or failure of the deletion.

        Raises:
            None

        Example:
            ```python
            user = "JohnDoe"
            account_id = 123

            result = Account.delete_account(user, account_id)
            print(result)
            ```
        """

        try:
            account = Account.objects.get(
                owner=user,
                id=id,
            )
        except ObjectDoesNotExist:
            return {"error": "Account not found"}

        account.delete()

        return {"success": "Account deleted successfully"}
