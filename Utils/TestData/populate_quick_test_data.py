#!/usr/bin/env python3
"""
Quick Test Data Population Script

A simplified version that creates minimal test data for quick testing.
Creates 2 accounts and 20 transactions for the testUser.

Usage:
    python populate_quick_test_data.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django environment
sys.path.append('../../API')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneyManagement.settings')
django.setup()

from users.models import User
from account.models import Account
from transaction.models import Transaction


def create_quick_test_data():
    """Create minimal test data for quick testing."""
    print("🚀 Creating quick test data...")
    
    # Check if test user exists
    try:
        user = User.objects.get(username="testUser")
        print(f"✅ Found user: {user.username}")
    except User.DoesNotExist:
        print("❌ testUser not found! Please create it first.")
        return False
    
    # Clear existing data
    Account.objects.filter(owner="testUser").delete()
    Transaction.objects.filter(owner_id="testUser").delete()
    print("🗑️  Cleared existing test data")
    
    # Create 2 accounts
    accounts = []
    
    # Checking account
    checking = Account.objects.create(
        account_type="Checking",
        bank="Chase Bank",
        total=2500.00,
        account_name="Chase Checking",
        owner="testUser"
    )
    accounts.append(checking)
    print(f"✅ Created: {checking.account_name} - ${checking.total}")
    
    # Savings account
    savings = Account.objects.create(
        account_type="Savings",
        bank="Bank of America",
        total=15000.00,
        account_name="BOA Savings",
        owner="testUser"
    )
    accounts.append(savings)
    print(f"✅ Created: {savings.account_name} - ${savings.total}")
    
    # Create 20 transactions
    transactions = [
        # Income transactions
        ("Income", "Salary", "Monthly Salary", 4500.00, checking.id),
        ("Income", "Freelance", "Freelance Work", 800.00, checking.id),
        ("Income", "Investment Returns", "Dividend Payment", 150.00, savings.id),
        
        # Expense transactions
        ("Expense", "Groceries", "Whole Foods", 120.50, checking.id),
        ("Expense", "Restaurants", "Starbucks", 8.75, checking.id),
        ("Expense", "Gas", "Shell Gas Station", 45.00, checking.id),
        ("Expense", "Utilities", "Electric Bill", 85.30, checking.id),
        ("Expense", "Rent/Mortgage", "Monthly Rent", 1200.00, checking.id),
        ("Expense", "Insurance", "Car Insurance", 120.00, checking.id),
        ("Expense", "Healthcare", "Doctor Visit", 25.00, checking.id),
        ("Expense", "Entertainment", "Netflix", 15.99, checking.id),
        ("Expense", "Shopping", "Amazon", 67.45, checking.id),
        ("Expense", "Transportation", "Uber", 12.50, checking.id),
        ("Expense", "Groceries", "Kroger", 89.20, checking.id),
        ("Expense", "Restaurants", "Pizza Hut", 24.99, checking.id),
        ("Expense", "Coffee", "Local Coffee Shop", 5.50, checking.id),
        ("Expense", "Phone", "Verizon Bill", 75.00, checking.id),
        ("Expense", "Internet", "Comcast", 65.00, checking.id),
        ("Expense", "Gym", "Planet Fitness", 10.00, checking.id),
    ]
    
    created_transactions = []
    start_date = datetime.now() - timedelta(days=30)  # Last 30 days
    
    for i, (trans_type, category, title, amount, account_id) in enumerate(transactions):
        # Random date within last 30 days
        random_days = random.randint(0, 30)
        transaction_date = start_date + timedelta(days=random_days)
        
        transaction = Transaction.objects.create(
            transaction_type=trans_type,
            category=category,
            date=transaction_date.date(),
            title=title,
            total=amount,
            owner_id="testUser",
            account_id=str(account_id)
        )
        created_transactions.append(transaction)
    
    print(f"✅ Created {len(created_transactions)} transactions")
    
    # Update account balances
    for account in accounts:
        account_transactions = [t for t in created_transactions if t.account_id == str(account.id)]
        current_balance = account.total
        
        for transaction in account_transactions:
            if transaction.transaction_type == "Income":
                current_balance += transaction.total
            else:
                current_balance -= transaction.total
        
        account.total = round(current_balance, 2)
        account.save()
        print(f"💰 Updated {account.account_name}: ${account.total}")
    
    print(f"\n🎉 Quick test data created successfully!")
    print(f"📊 Summary:")
    print(f"  • 2 accounts created")
    print(f"  • {len(created_transactions)} transactions created")
    print(f"  • Data covers last 30 days")
    print(f"\n🔗 Test the application at: http://localhost:8080")
    print(f"👤 Login with: testUser / testpass123")
    
    return True


if __name__ == "__main__":
    success = create_quick_test_data()
    if not success:
        sys.exit(1)
