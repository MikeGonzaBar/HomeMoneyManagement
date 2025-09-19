from django.urls import path
from . import views

urlpatterns = [
    path("", views.AccountCreate.as_view(), name="account_create"),
    path(
        "details/<str:user>/<str:id>/",
        views.AccountOps.as_view(),
        name="account_details",
    ),
    path(
        "delete/<str:user>/<str:id>/",
        views.AccountDelete.as_view(),
        name="account_delete",
    ),
]
