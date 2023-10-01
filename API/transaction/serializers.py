from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer class for the Transaction model.

    Fields:
        transaction_type (str): The type of the transaction.
        category (str): The category of the transaction.
        date (date): The date of the transaction.
        title (str): The title of the transaction.
        total (float): The total amount of the transaction.
        owner_id (str): The ID of the owner of the transaction.
        account_id (str): The ID of the account associated with the transaction.
    """
    class Meta:
        """
        Meta class for the TransactionSerializer.

        Attributes:
            model (class): The model class associated with the serializer.
            fields (tuple): The fields to include in the serialized representation.
        """
        model = Transaction
        fields = (
            "transaction_type",
            "category",
            "date",
            "title",
            "total",
            "owner_id",
            "account_id",
        )
