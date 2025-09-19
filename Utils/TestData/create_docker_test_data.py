#!/usr/bin/env python3
"""
Simple test data creation script for Docker container
"""

import os
import django

# Setup Django environment
import sys
sys.path.append('../../API')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneyManagement.settings')
django.setup()

from users.models import User
from account.models import Account
from transaction.models import Transaction
from datetime import datetime, timedelta
import random

def create_test_data():
    print('🚀 Creating test data in Docker container...')
    
    # Clear existing data
    Account.objects.filter(owner='testUser').delete()
    Transaction.objects.filter(owner_id='testUser').delete()
    print('🗑️  Cleared existing test data')
    
    # Create accounts
    checking = Account.objects.create(
        account_type='Checking',
        bank='Chase Bank',
        total=2500.00,
        account_name='Chase Checking',
        owner='testUser'
    )
    print(f'✅ Created: {checking.account_name} - ${checking.total}')
    
    savings = Account.objects.create(
        account_type='Savings',
        bank='Bank of America',
        total=15000.00,
        account_name='BOA Savings',
        owner='testUser'
    )
    print(f'✅ Created: {savings.account_name} - ${savings.total}')
    
    # Create sample transactions
    transactions = [
        ('Income', 'Salary', 'Monthly Salary', 4500.00, checking.id),
        ('Expense', 'Groceries', 'Whole Foods', 120.50, checking.id),
        ('Expense', 'Restaurants', 'Starbucks', 8.75, checking.id),
        ('Expense', 'Gas', 'Shell Gas Station', 45.00, checking.id),
        ('Expense', 'Utilities', 'Electric Bill', 85.30, checking.id),
        ('Expense', 'Rent/Mortgage', 'Monthly Rent', 1200.00, checking.id),
        ('Expense', 'Insurance', 'Car Insurance', 120.00, checking.id),
        ('Expense', 'Healthcare', 'Doctor Visit', 25.00, checking.id),
        ('Expense', 'Entertainment', 'Netflix', 15.99, checking.id),
        ('Expense', 'Shopping', 'Amazon', 67.45, checking.id),
        ('Expense', 'Transportation', 'Uber', 12.50, checking.id),
        ('Expense', 'Groceries', 'Kroger', 89.20, checking.id),
        ('Expense', 'Restaurants', 'Pizza Hut', 24.99, checking.id),
        ('Expense', 'Coffee', 'Local Coffee Shop', 5.50, checking.id),
        ('Expense', 'Phone', 'Verizon Bill', 75.00, checking.id),
        ('Expense', 'Internet', 'Comcast', 65.00, checking.id),
        ('Expense', 'Gym', 'Planet Fitness', 10.00, checking.id),
        ('Income', 'Freelance', 'Freelance Work', 800.00, checking.id),
        ('Income', 'Investment Returns', 'Dividend Payment', 150.00, savings.id),
    ]
    
    created_transactions = []
    start_date = datetime.now() - timedelta(days=30)
    
    for i, (trans_type, category, title, amount, account_id) in enumerate(transactions):
        random_days = random.randint(0, 30)
        transaction_date = start_date + timedelta(days=random_days)
        
        transaction = Transaction.objects.create(
            transaction_type=trans_type,
            category=category,
            date=transaction_date.date(),
            title=title,
            total=amount,
            owner_id='testUser',
            account_id=str(account_id)
        )
        created_transactions.append(transaction)
    
    print(f'✅ Created {len(created_transactions)} transactions')
    
    # Update account balances
    for account in [checking, savings]:
        account_transactions = [t for t in created_transactions if t.account_id == str(account.id)]
        current_balance = account.total
        
        for transaction in account_transactions:
            if transaction.transaction_type == 'Income':
                current_balance += transaction.total
            else:
                current_balance -= transaction.total
        
        account.total = round(current_balance, 2)
        account.save()
        print(f'💰 Updated {account.account_name}: ${account.total}')
    
    print('🎉 Test data created successfully in Docker container!')
    print('🔗 You can now access the application and login with: testUser / testpass123')

if __name__ == '__main__':
    create_test_data()
