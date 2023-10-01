from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer class for the User model.

    Attributes:
        model (class): The User model.
        fields (tuple): The fields to include in the serialized representation of the User model.
    """

    class Meta:
        """
        Meta class for defining the model and fields used in a serializer.

        Attributes:
            model (class): The model to be serialized.
            fields (tuple): The fields to include in the serialized representation of the model.
        """

        model = User
        fields = (
            "username",
            "password",
            "first_name",
            "last_name",
        )
