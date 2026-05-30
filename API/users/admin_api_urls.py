"""URL routes for API admin-mode endpoints."""

from django.urls import path

from .admin_api_views import AdminUserDetail, AdminUserList, AdminUserTokenRevoke


urlpatterns = [
    path("users/", AdminUserList.as_view(), name="api_admin_user_list"),
    path("users/<int:user_id>/", AdminUserDetail.as_view(), name="api_admin_user_detail"),
    path(
        "users/<int:user_id>/tokens/revoke/",
        AdminUserTokenRevoke.as_view(),
        name="api_admin_user_tokens_revoke",
    ),
]
