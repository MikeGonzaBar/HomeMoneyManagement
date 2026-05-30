from django.contrib import admin
from django.contrib.admin.utils import get_deleted_objects
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Django admin configuration for token-auth API users."""

    list_display = ('id', 'username', 'first_name', 'last_name', 'is_admin', 'related_objects_count')
    list_filter = ('first_name', 'last_name', 'is_admin')
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('id', 'related_objects_count')
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'is_admin')
        }),
        ('Related Data', {
            'fields': ('related_objects_count',),
            'description': 'Summary of related objects that will be deleted with this user.'
        }),
    )
    
    def related_objects_count(self, obj: User | None) -> str:
        """Display count of related objects."""
        if not obj or not obj.pk:
            return "N/A"
        
        from account.models import Account
        from transaction.models import Transaction
        from bankstatements.models import BankStatement
        
        accounts_count = Account.objects.filter(owner_user=obj).count()
        transactions_count = Transaction.objects.filter(owner_user=obj).count()
        statements_count = BankStatement.objects.filter(owner_user=obj).count()
        
        return format_html(
            '<strong>Accounts:</strong> {}<br/>'
            '<strong>Transactions:</strong> {}<br/>'
            '<strong>Bank Statements:</strong> {}',
            accounts_count, transactions_count, statements_count
        )
    related_objects_count.short_description = 'Related Objects'
    
    def get_deleted_objects(self, objs: list[User], request: HttpRequest) -> tuple:
        """Override to show related objects in delete confirmation."""
        from account.models import Account
        from transaction.models import Transaction
        from bankstatements.models import BankStatement
        
        # Get the standard deleted objects
        deleted_objects, model_count, perms_needed, protected = get_deleted_objects(
            objs, request, self.admin_site
        )
        
        # Add related objects manually since we're using CharField instead of ForeignKey
        for obj in objs:
            # Get related accounts
            accounts = list(Account.objects.filter(owner_user=obj))
            if accounts:
                if 'account' not in model_count:
                    model_count['account'] = 0
                model_count['account'] += len(accounts)
                # Add to deleted_objects list
                deleted_objects.append(('account', 'Account', accounts))
            
            # Get related transactions
            transactions = list(Transaction.objects.filter(owner_user=obj))
            if transactions:
                if 'transaction' not in model_count:
                    model_count['transaction'] = 0
                model_count['transaction'] += len(transactions)
                deleted_objects.append(('transaction', 'Transaction', transactions))
            
            # Get related bank statements
            statements = list(BankStatement.objects.filter(owner_user=obj))
            if statements:
                if 'bankstatements' not in model_count:
                    model_count['bankstatements'] = 0
                model_count['bankstatements'] += len(statements)
                deleted_objects.append(('bankstatements', 'Bank Statement', statements))
        
        return deleted_objects, model_count, perms_needed, protected
    
    def delete_model(self, request: HttpRequest, obj: User) -> None:
        """Override delete to cascade delete related objects."""
        from account.models import Account
        from transaction.models import Transaction
        from bankstatements.models import BankStatement
        
        # Delete related bank statements (and their files)
        statements = BankStatement.objects.filter(owner_user=obj)
        for statement in statements:
            statement.delete()  # This will also delete the file
        
        # Delete related transactions
        Transaction.objects.filter(owner_user=obj).delete()
        
        # Delete related accounts
        Account.objects.filter(owner_user=obj).delete()
        
        # Finally, delete the user
        obj.delete()
    
    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        """Override to handle bulk delete with cascade."""
        for obj in queryset:
            self.delete_model(request, obj)
