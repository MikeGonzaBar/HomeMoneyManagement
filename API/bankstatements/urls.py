from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_bank_statement, name='upload_bank_statement'),
    path('user/<str:user_id>/', views.get_user_bank_statements, name='get_user_bank_statements'),
    path('details/<int:statement_id>/', views.get_bank_statement_details, name='get_bank_statement_details'),
    path('delete/<int:statement_id>/', views.delete_bank_statement, name='delete_bank_statement'),
    path('import-batches/<int:batch_id>/', views.get_import_batch, name='get_import_batch'),
    path('import-candidates/<int:candidate_id>/', views.update_import_candidate, name='update_import_candidate'),
    path('import-batches/<int:batch_id>/commit/', views.commit_import_batch, name='commit_import_batch'),
]
