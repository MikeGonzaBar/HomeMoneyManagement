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
        total (Decimal): The total amount of the transaction.
        owner_id (str): Legacy username mirror of the authenticated owner.
        owner_user (User): Authoritative owner foreign key.
        account_id (str): Legacy account ID mirror for income/expense transactions.
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
            "id",
            "transaction_type",
            "category",
            "date",
            "title",
            "total",
            "owner_id",
            "owner_user",
            "account_id",
            "account_fk",
            "from_account_id",
            "from_account_fk",
            "to_account_id",
            "to_account_fk",
        )
        read_only_fields = ("id", "owner_id", "owner_user", "account_fk", "from_account_fk", "to_account_fk")
