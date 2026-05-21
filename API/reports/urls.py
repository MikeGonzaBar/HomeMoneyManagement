from django.urls import path
from . import views

urlpatterns = [
    path(
        "analytics/<str:username>/",
        views.ReportsAnalytics.as_view(),
        name="reports_analytics",
    ),
    path(
        "insights/<str:username>/",
        views.ReportsInsights.as_view(),
        name="reports_insights",
    ),
    path(
        "forecast/<str:username>/",
        views.ReportsForecast.as_view(),
        name="reports_forecast",
    ),
]
