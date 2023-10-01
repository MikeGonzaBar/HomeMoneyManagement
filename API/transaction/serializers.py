from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
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
