from django.urls import path
from . import views

urlpatterns = [
    path("", views.AccountCreate.as_view(), name="account_post"),
    path(
        "details/<str:user>/",
        views.AccountOps.as_view(),
        name="User_detail",
    ),
    path(
        "delete/<str:user>/<str:id>/",
        views.AccountDelete.as_view(),
        name="User_detail",
    ),
]
