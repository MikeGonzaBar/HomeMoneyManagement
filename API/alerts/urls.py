from django.urls import path

from . import views


urlpatterns = [
    path("", views.AlertList.as_view(), name="alert_list"),
    path("refresh/", views.AlertRefresh.as_view(), name="alert_refresh"),
    path("<int:alert_id>/read/", views.AlertRead.as_view(), name="alert_read"),
    path("<int:alert_id>/dismiss/", views.AlertDismiss.as_view(), name="alert_dismiss"),
]
