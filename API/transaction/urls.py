from django.urls import path
from .views import (
    TransactionCreate,
    TransactionRetrieve,
    TransactionUpdate,
    TransactionDelete,
)

urlpatterns = [
    path("create/", TransactionCreate.as_view(), name="transaction_create"),
    path(
        "retrieve/<str:user>/<str:account_id>/<int:month>/<int:year>/",
        TransactionRetrieve.as_view(),
        name="transaction_retrieve",
    ),
    path(
        "update/<str:transaction_id>/",
        TransactionUpdate.as_view(),
        name="transaction_update",
    ),
    path(
        "delete/<str:transaction_id>/",
        TransactionDelete.as_view(),
        name="transaction_delete",
    ),
]
