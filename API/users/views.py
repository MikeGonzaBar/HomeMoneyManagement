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
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )


class UserDetail(generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request: HttpRequest, user: str) -> HttpResponse:
        return HttpResponse(
            json.dumps({"error:get method not valid"}, default=str),
            status=403,
            content_type="application/json",
        )

    def post(self, request: HttpRequest, user: str) -> HttpResponse:
        data = json.loads(request.body)
        response = User.login(user, data)
        new_status = 400 if response["valid"] == False else 200
        return HttpResponse(
            response,
            status=new_status,
        )

    def delete(self, request: HttpRequest, user: str) -> HttpResponse:
        data = json.loads(request.body)
        response = User.delete_user(user, data)
        status = 400 if "error" in response else 200
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )
