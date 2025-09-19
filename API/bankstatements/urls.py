from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_bank_statement, name='upload_bank_statement'),
    path('user/<str:user_id>/', views.get_user_bank_statements, name='get_user_bank_statements'),
    path('details/<int:statement_id>/', views.get_bank_statement_details, name='get_bank_statement_details'),
    path('delete/<int:statement_id>/', views.delete_bank_statement, name='delete_bank_statement'),
]
