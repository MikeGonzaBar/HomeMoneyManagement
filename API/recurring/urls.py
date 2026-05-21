from django.urls import path

from . import views


urlpatterns = [
    path("", views.RecurringListCreate.as_view(), name="recurring_list_create"),
    path("due/", views.RecurringDue.as_view(), name="recurring_due"),
    path("due/<int:occurrence_id>/post/", views.RecurringPostDue.as_view(), name="recurring_post_due"),
    path("due/<int:occurrence_id>/skip/", views.RecurringSkipDue.as_view(), name="recurring_skip_due"),
    path("<int:recurring_id>/", views.RecurringDetail.as_view(), name="recurring_detail"),
]
