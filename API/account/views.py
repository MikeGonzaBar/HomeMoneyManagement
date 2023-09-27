import json
from django.http import HttpRequest, HttpResponse
from rest_framework import generics
from .models import Account
from .serializers import AccountSerializer


# Create your views here.
class AccountCreate(generics.CreateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def post(self, request: HttpRequest) -> HttpResponse:
        data = json.loads(request.body)
        response = Account.create_account(data)
        status = 400 if "error" in response else 201
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )


class AccountOps(generics.RetrieveUpdateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def get(self, request: HttpRequest, user: str) -> HttpResponse:
        response = Account.get_accounts(user)
        return HttpResponse(
            json.dumps(response, default=str),
            status=200,
            content_type="application/json",
        )

    def patch(self, request: HttpRequest, user: str) -> HttpResponse:
        data = json.loads(request.body)
        response = Account.update_account(user, data)
        return HttpResponse(
            json.dumps(response, default=str),
            status=200,
            content_type="application/json",
        )

class AccountDelete(generics.DestroyAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    def delete(
        self, request: HttpRequest, user: str, id:str) -> HttpResponse:
        response = Account.delete_account(user, id)
        status = 400 if "error" in response else 200
        return HttpResponse(
            json.dumps(response, default=str),
            status=status,
            content_type="application/json",
        )
        
