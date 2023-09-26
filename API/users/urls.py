from django.urls import path
from . import views

urlpatterns = [
    path("", views.UserPostGet.as_view(), name="user_post"),
    path(
        "<str:user>/",
        views.UserDetail.as_view(),
        name="User_detail",
    ),
]
