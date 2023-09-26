from django.db import models


class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    @staticmethod
    def find_missing_data(data_dict: dict):
        keys_to_check = ["username", "password", "first_name", "last_name"]
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
    def create_user(data: dict):
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
    def login(user, data: dict):
        query = User.objects.filter(username=user)

        if query.count() <= 0:
            return {"valid": False}

        array_users = User.queryset_to_array_of_dicts(query)
        user = array_users[0]
        logged = user["password"] == data["password"]
        return {"valid": logged}

    @staticmethod
    def delete_user(user, data):
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
