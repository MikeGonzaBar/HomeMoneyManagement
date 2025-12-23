from django.contrib import admin
from django.contrib.admin.utils import get_deleted_objects
from django.contrib.admin import helpers
from django.utils.html import format_html
from django.urls import reverse
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'related_objects_count')
    list_filter = ('first_name', 'last_name')
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('id', 'related_objects_count')
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name')
        }),
        ('Related Data', {
            'fields': ('related_objects_count',),
            'description': 'Summary of related objects that will be deleted with this user.'
        }),
    )
    
    def related_objects_count(self, obj):
        """Display count of related objects."""
        if not obj or not obj.pk:
            return "N/A"
        
        from account.models import Account
        from transaction.models import Transaction
        from bankstatements.models import BankStatement
        
        accounts_count = Account.objects.filter(owner=obj.username).count()
        transactions_count = Transaction.objects.filter(owner_id=str(obj.id)).count()
        statements_count = BankStatement.objects.filter(user_id=obj.username).count()
        
        return format_html(
            '<strong>Accounts:</strong> {}<br/>'
            '<strong>Transactions:</strong> {}<br/>'
            '<strong>Bank Statements:</strong> {}',
            accounts_count, transactions_count, statements_count
        )
    related_objects_count.short_description = 'Related Objects'
    
    def get_deleted_objects(self, objs, request):
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
            accounts = list(Account.objects.filter(owner=obj.username))
            if accounts:
                if 'account' not in model_count:
                    model_count['account'] = 0
                model_count['account'] += len(accounts)
                # Add to deleted_objects list
                deleted_objects.append(('account', 'Account', accounts))
            
            # Get related transactions
            transactions = list(Transaction.objects.filter(owner_id=str(obj.id)))
            if transactions:
                if 'transaction' not in model_count:
                    model_count['transaction'] = 0
                model_count['transaction'] += len(transactions)
                deleted_objects.append(('transaction', 'Transaction', transactions))
            
            # Get related bank statements
            statements = list(BankStatement.objects.filter(user_id=obj.username))
            if statements:
                if 'bankstatements' not in model_count:
                    model_count['bankstatements'] = 0
                model_count['bankstatements'] += len(statements)
                deleted_objects.append(('bankstatements', 'Bank Statement', statements))
        
        return deleted_objects, model_count, perms_needed, protected
    
    def delete_model(self, request, obj):
        """Override delete to cascade delete related objects."""
        from account.models import Account
        from transaction.models import Transaction
        from bankstatements.models import BankStatement
        
        username = obj.username
        user_id = str(obj.id)
        
        # Delete related bank statements (and their files)
        statements = BankStatement.objects.filter(user_id=username)
        for statement in statements:
            statement.delete()  # This will also delete the file
        
        # Delete related transactions
        Transaction.objects.filter(owner_id=user_id).delete()
        
        # Delete related accounts
        Account.objects.filter(owner=username).delete()
        
        # Finally, delete the user
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        """Override to handle bulk delete with cascade."""
        for obj in queryset:
            self.delete_model(request, obj)
