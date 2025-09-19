from django.urls import path
from . import views

urlpatterns = [
    # New secure endpoints
    path("register/", views.UserRegistrationView.as_view(), name="user_register"),
    path("login/", views.UserLoginView.as_view(), name="user_login"),
    path("profile/", views.user_profile, name="user_profile"),
    
    # Profile management endpoints
    path("update-info/", views.update_user_info, name="update_user_info"),
    path("change-password/", views.change_password, name="change_password"),
    
    # Backward compatibility endpoints
    path("", views.UserRegistrationView.as_view(), name="user_register_legacy"),
    path("<str:username>/", views.UserLoginView.as_view(), name="user_login_legacy"),
    
    # User detail endpoint (for authenticated users)
    path("detail/<str:username>/", views.UserDetailView.as_view(), name="user_detail"),
]
