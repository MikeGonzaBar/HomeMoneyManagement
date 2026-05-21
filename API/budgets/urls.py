from django.urls import path

from . import views


urlpatterns = [
    path("", views.BudgetListCreate.as_view(), name="budget_list_create"),
    path("summary/", views.BudgetSummary.as_view(), name="budget_summary"),
    path("<int:budget_id>/", views.BudgetDetail.as_view(), name="budget_detail"),
]
