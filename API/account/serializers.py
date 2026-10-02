from rest_framework import serializers
from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializes the Account model for API responses.

    Attributes:
        model (Account): The Account model to serialize.
        fields (tuple): The fields to include in the serialized representation.
    """

    class Meta:
        """
        Specifies the metadata for the AccountSerializer class.

        Attributes:
            model (Account): The Account model to serialize.
            fields (tuple): The fields to include in the serialized representation.
        """
        model = Account
        fields = (
            "id",
            "account_type",
            "bank",
            "total",
            "account_name",
            "owner",
            "owner_user",
            "credit_limit",
            "retirement_metadata",
            "credit_card_metadata",
        )
        read_only_fields = ("id", "owner", "owner_user")
