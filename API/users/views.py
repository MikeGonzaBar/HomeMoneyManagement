import json
from django.http import HttpRequest, HttpResponse
from rest_framework import generics
from .models import User
from .serializers import UserSerializer


class UserPostGet(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def post(self, request: HttpRequest) -> HttpResponse:
        data = json.loads(request.body)
        response = User.create_user(data)
        status = 400 if "error" in response else 201
        response = HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )
        return self.add_CORS_data(response)

    def options(self, request, *args, **kwargs):
        response = HttpResponse()
        return self.add_CORS_data(response)

    def add_CORS_data(self, response):
        response["Access-Control-Allow-Origin"] = "http://127.0.0.1:3000"
        response["Access-Control-Allow-Methods"] = "POST"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response


class UserDetail(generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request: HttpRequest, user: str) -> HttpResponse:
        return HttpResponse(
            json.dumps({"error:get method not valid"}, default=str),
            status=403,
            content_type="application/json",
        )

    def options(self, request, *args, **kwargs):
        response = HttpResponse()
        return self.add_CORS_data(response)

    def post(self, request: HttpRequest, user: str) -> HttpResponse:
        print("user", user)
        data = json.loads(request.body)
        print("pwd", data)
        response = User.login(user, data)
        new_status = 400 if response["valid"] == False else 200
        response = HttpResponse(
            json.dumps(response, default=str),
            status=new_status,
            content_type="application/json",
        )
        return self.add_CORS_data(response)

    def add_CORS_data(self, response):
        response[
            "Access-Control-Allow-Origin"
        ] = "http://127.0.0.1:3000 http://localhost:3000"

        response["Access-Control-Allow-Methods"] = "POST"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    def delete(self, request: HttpRequest, user: str) -> HttpResponse:
        data = json.loads(request.body)
        response = User.delete_user(user, data)
        status = 400 if "error" in response else 200
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )
