from typing import Optional
from django.db import models


class User(models.Model):
    """
    Model class representing a User.

    Attributes:
        id (AutoField): The primary key of the user.
        username (CharField): The username of the user.
        password (CharField): The password of the user.
        first_name (CharField): The first name of the user.
        last_name (CharField): The last name of the user.

    Methods:
        find_missing_data(data_dict: dict) -> list[str]: Finds missing data in the provided data dictionary.
        queryset_to_array_of_dicts(queryset: QuerySet, fields=None) -> list[dict]: Converts a queryset to a list of dictionaries.
        create_user(data: dict) -> dict: Creates a new user with the provided data.
        login(user, data: dict) -> dict: Performs user login with the provided username and password.
        delete_user(user, data) -> dict: Deletes a user with the provided username and password.
    """

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    @staticmethod
    def find_missing_data(data_dict: dict) -> list:
        """
        Finds missing data in a given data dictionary.

        Args:
            data_dict (dict): A dictionary containing data.

        Returns:
            list: A list of keys from `keys_to_check` that are missing from `data_dict` or have a falsy value.

        Example:
            ```python
            data = {
                "username": "john_doe",
                "password": "",
                "first_name": "John",
                "last_name": None
            }

            missing_data = find_missing_data(data)
            print(missing_data)  # Output: ['password', 'last_name']
            ```
        """

        keys_to_check = ["username", "password", "first_name", "last_name"]
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
            queryset (models.query.QuerySet): The QuerySet to convert.
            fields (Optional[list[str]], optional): A list of fields to include in the dictionaries. If not provided, all fields of the model will be included. Defaults to None.

        Returns:
            list[dict]: An array of dictionaries representing the objects in the QuerySet.

        Example:
            ```python
            queryset = MyModel.objects.all()
            fields = ["name", "age"]

            result = queryset_to_array_of_dicts(queryset, fields)
            print(result)  # Output: [{'name': 'John', 'age': 25}, {'name': 'Jane', 'age': 30}]
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
    def create_user(data: dict) -> dict:
        """
        Creates a new user based on the provided data.

        Args:
            data (dict): A dictionary containing the user data. It should include the following keys: "username", "password", "first_name", "last_name".

        Returns:
            dict: A dictionary representing the created user. If the data is incomplete or the username already exists, an error message is returned instead.

        Example:
            ```python
            data = {
                "username": "john_doe",
                "password": "password123",
                "first_name": "John",
                "last_name": "Doe"
            }

            user = create_user(data)
            print(user)  # Output: {'username': 'john_doe', 'password': 'password123', 'first_name': 'John', 'last_name': 'Doe', 'status': 'User saved'}
            ```
        """
        missing_keys = User.find_missing_data(data)

        if len(missing_keys) > 0:
            return {"error": "data incomplete", "missing_args": missing_keys}
        if User.objects.filter(username=data["username"]).exists():
            return {"error": "Username already exists"}

        new_user = User(
            username=data["username"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        new_user.save()

        query = User.objects.filter(username=data["username"])

        response = User.queryset_to_array_of_dicts(query)
        response[0]["status"] = "User saved"
        return response[0]

    @staticmethod
    def login(user, data: dict) -> dict:
        """
        Logs in a user with the provided data.

        Args:
            user (str): The username of the user to log in.
            data (dict): A dictionary containing the login data. It should include the following key: "password".

        Returns:
            dict: A dictionary indicating whether the login was successful. If the user does not exist or the password is incorrect, the "valid" key will be False. If the login is successful, the "valid" key will be True and the "id" key will contain the user's ID.

        Example:
            ```python
            user = "john_doe"
            login_data = {
                "password": "password123"
            }

            result = login(user, login_data)
            print(result)  # Output: {'valid': True, 'id': 123}
            ```
        """
        user = User.objects.get(username=user)
        logged = user.password == data.get("password")
        return {"valid": logged, "id": user["id"]}

    @staticmethod
    def delete_user(user: str, data: dict) -> dict:
        """
        Deletes a user based on the provided data.

        Args:
            user (str): The username of the user to delete.
            data (dict): A dictionary containing the deletion data. It should include the following key: "password".

        Returns:
            dict: A dictionary representing the deleted user if the password is correct. If the password is incorrect or the user does not exist, an error message is returned.

        Example:
            ```python
            user = "john_doe"
            deletion_data = {
                "password": "password123"
            }

            result = delete_user(user, deletion_data)
            print(result)  # Output: {'username': 'john_doe', 'status': 'user deleted'}
            ```
        """
        if data is None:
            return {"error": "Password incorrect"}
        user_to_delete = User.objects.filter(username=user)
        if len(user_to_delete) == 0:
            return {"error": "User not found"}

        t_user = User.queryset_to_array_of_dicts(user_to_delete)
        if t_user[0]["password"] == data["password"]:
            user_to_delete.delete()
            t_user[0]["status"] = "user deleted"
            return t_user[0]
        return {"error": "Password incorrect"}
