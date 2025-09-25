#!/usr/bin/env python3
"""
Test Data Population Script for Home Money Management API

This script populates the database with realistic test data for the testUser.
It creates multiple accounts and transactions with varied data to simulate
real-world usage patterns.

Usage:
    python populate_test_data.py

Requirements:
    - testUser must exist in the database
    - Django environment must be set up
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Setup Django environment
sys.path.append('../../API')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneyManagement.settings')
django.setup()

# Import Django models (path resolved at runtime)
from users.models import User  # type: ignore
from account.models import Account  # type: ignore
from transaction.models import Transaction  # type: ignore


class TestDataGenerator:
    """Generates realistic test data for the Home Money Management application."""
    
    def __init__(self):
        self.test_username = "testUser"
        self.user = None
        
        # Realistic data pools
        self.banks = [
            "Chase Bank", "Bank of America", "Wells Fargo", "Citibank", 
            "Capital One", "PNC Bank", "US Bank", "TD Bank", "HSBC", "BB&T"
        ]
        
        # Account types that match the UI (Spanish labels with English values)
        self.account_types = ["Débito", "Crédito", "Efectivo"]
        
        # Income categories that match the UI
        self.income_categories = [
            "Salary", "Awards", "Investments", "Others"
        ]
        
        # Expense categories that match the UI
        self.expense_categories = [
            "Bills and utilities", "Education", "Entertainment", "Food and drinks",
            "Gifts", "Insurance", "Investments", "Loans", "Medical", "Others",
            "Shopping", "Transportation"
        ]
        
        # Transfer categories
        self.transfer_categories = [
            "Transfer", "Account Transfer", "Money Transfer", "Balance Transfer"
        ]
        
        # Transaction titles that match the UI categories
        self.transaction_titles = {
            "Food and drinks": [
                "Whole Foods", "Kroger", "Safeway", "Trader Joe's", "Costco",
                "Walmart", "Target", "McDonald's", "Starbucks", "Pizza Hut", 
                "Subway", "Chipotle", "Local Diner", "Fine Dining", "Coffee Shop"
            ],
            "Transportation": [
                "Uber", "Lyft", "Taxi", "Bus Pass", "Train Ticket",
                "Parking Fee", "Toll Road", "Car Rental", "Shell Gas", "Exxon Gas"
            ],
            "Bills and utilities": [
                "Electric Bill", "Water Bill", "Gas Bill", "Internet Bill",
                "Cable Bill", "Trash Service", "Sewer Bill", "Phone Bill",
                "Comcast", "Verizon Fios", "AT&T Internet", "Spectrum"
            ],
            "Insurance": [
                "Car Insurance", "Health Insurance", "Home Insurance",
                "Life Insurance", "Renters Insurance"
            ],
            "Medical": [
                "Doctor Visit", "Pharmacy", "Dental Checkup", "Eye Exam",
                "Prescription", "Emergency Room", "Specialist Visit"
            ],
            "Entertainment": [
                "Netflix", "Spotify", "Movie Theater", "Concert", "Sports Game",
                "Video Games", "Books", "Magazine Subscription"
            ],
            "Shopping": [
                "Amazon", "Target", "Walmart", "Best Buy", "Macy's",
                "Nike", "Apple Store", "Local Boutique"
            ],
            "Education": [
                "Tuition", "Textbooks", "Online Course", "Certification",
                "Workshop", "Conference", "Training"
            ],
            "Investments": [
                "Stock Purchase", "Mutual Fund", "ETF", "Bond", "Dividend",
                "Investment Return", "Portfolio Management"
            ],
            "Loans": [
                "Student Loan", "Car Loan", "Personal Loan", "Credit Card Payment",
                "Mortgage Payment", "Loan Interest"
            ],
            "Gifts": [
                "Birthday Gift", "Wedding Gift", "Holiday Gift", "Charity Donation",
                "Gift Card", "Flowers"
            ],
            "Others": [
                "ATM Withdrawal", "Cash Deposit", "Transfer", "Fee",
                "Refund", "Miscellaneous", "Unknown Transaction"
            ],
            "Salary": [
                "Monthly Salary", "Bi-weekly Pay", "Payroll", "Direct Deposit",
                "Overtime Pay", "Holiday Pay"
            ],
            "Awards": [
                "Bonus", "Commission", "Performance Award", "Recognition Bonus",
                "Sales Commission", "Achievement Award"
            ]
        }
    
    def get_or_create_test_user(self):
        """Get or create the test user."""
        try:
            self.user = User.objects.get(username=self.test_username)
            print(f"✅ Found existing user: {self.user.username}")
        except User.DoesNotExist:
            print(f"❌ User '{self.test_username}' not found!")
            print("Please create the test user first using:")
            print("python create_test_user.py")
            return False
        return True
    
    def create_accounts(self, num_accounts=4):
        """Create multiple accounts for the test user."""
        print(f"\n🏦 Creating {num_accounts} accounts...")
        
        # Clear existing accounts for test user
        Account.objects.filter(owner=self.test_username).delete()
        print("🗑️  Cleared existing accounts for test user")
        
        accounts_created = []
        
        # Create one account of each type to match UI
        for i in range(num_accounts):
            account_type = self.account_types[i]  # Use each type in order
            bank = random.choice(self.banks)
            
            # Generate realistic account names based on UI account types
            if account_type == "Débito":
                # Debit accounts (like checking/savings) - should be positive
                account_name = f"{bank} Débito"
                base_balance = random.uniform(1000, 8000)  # Higher positive balance
            elif account_type == "Crédito":
                # Credit card accounts - positive = available credit, negative = debt
                account_name = f"{bank} Crédito"
                credit_limit = random.uniform(5000, 15000)  # Credit limit
                used_credit = random.uniform(1000, credit_limit * 0.7)  # Used credit (up to 70% of limit)
                base_balance = credit_limit - used_credit  # Available credit
            elif account_type == "Efectivo":
                # Cash accounts - should be positive
                account_name = "Efectivo"
                base_balance = random.uniform(100, 2000)  # Positive cash
            
            # Create account with credit limit for credit cards
            account_data = {
                'account_type': account_type,
                'bank': bank,
                'total': round(base_balance, 2),
                'account_name': account_name,
                'owner': self.test_username
            }
            
            # Add credit limit for credit card accounts
            if account_type == "Crédito":
                account_data['credit_limit'] = round(credit_limit, 2)
            
            account = Account.objects.create(**account_data)
            
            accounts_created.append(account)
            print(f"  ✅ Created: {account.account_name} - ${account.total:,.2f}")
        
        return accounts_created
    
    def create_transactions(self, accounts, num_transactions=100):
        """Create realistic transactions for the accounts."""
        print(f"\n💰 Creating {num_transactions} transactions...")
        
        # Clear existing transactions for test user
        Transaction.objects.filter(owner_id=self.test_username).delete()
        print("🗑️  Cleared existing transactions for test user")
        
        transactions_created = []
        start_date = datetime.now() - timedelta(days=365)  # Last year
        
        for i in range(num_transactions):
            # Random date within the last year
            random_days = random.randint(0, 365)
            transaction_date = start_date + timedelta(days=random_days)
            
            # Choose random account
            account = random.choice(accounts)
            account_id = str(account.id)
            
            # 50% expense, 30% income, 20% transfer
            rand = random.random()
            if rand < 0.5:
                # Expense transaction
                transaction_type = "Expense"
                category = random.choice(self.expense_categories)
                
                # Generate realistic expense amounts based on UI categories
                if category == "Food and drinks":
                    amount = random.uniform(5, 200)  # Coffee to groceries
                elif category == "Transportation":
                    amount = random.uniform(10, 100)  # Gas, parking, rides
                elif category == "Bills and utilities":
                    amount = random.uniform(50, 300)  # Monthly bills
                elif category == "Insurance":
                    amount = random.uniform(100, 500)  # Monthly insurance
                elif category == "Medical":
                    amount = random.uniform(50, 500)  # Medical expenses
                elif category == "Entertainment":
                    amount = random.uniform(10, 100)  # Movies, subscriptions
                elif category == "Shopping":
                    amount = random.uniform(20, 500)  # Retail purchases
                elif category == "Education":
                    amount = random.uniform(50, 500)  # Tuition, courses (reduced)
                elif category == "Investments":
                    amount = random.uniform(50, 1000)  # Investment amounts (reduced)
                elif category == "Loans":
                    amount = random.uniform(100, 800)  # Loan payments (reduced)
                elif category == "Gifts":
                    amount = random.uniform(20, 200)  # Gift amounts
                else:  # Others
                    amount = random.uniform(10, 200)
                
                # Generate title based on category
                if category in self.transaction_titles:
                    title = random.choice(self.transaction_titles[category])
                else:
                    title = f"{category} Payment"
                
                # Create expense transaction
                transaction = Transaction.objects.create(
                    transaction_type=transaction_type,
                    category=category,
                    date=transaction_date.date(),
                    title=title,
                    total=round(amount, 2),
                    owner_id=self.test_username,
                    account_id=account_id
                )
                
            elif rand < 0.8:  # 30% income
                # Income transaction
                transaction_type = "Income"
                category = random.choice(self.income_categories)
                
                # Generate realistic income amounts based on UI categories
                if category == "Salary":
                    amount = random.uniform(2000, 8000)  # Monthly salary
                elif category == "Awards":
                    amount = random.uniform(500, 5000)  # Bonuses, commissions
                elif category == "Investments":
                    amount = random.uniform(50, 2000)  # Investment returns
                else:  # Others
                    amount = random.uniform(100, 1000)  # Miscellaneous income
                
                # Generate title based on category
                if category in self.transaction_titles:
                    title = random.choice(self.transaction_titles[category])
                else:
                    title = f"{category} Payment"
                
                # Create income transaction
                transaction = Transaction.objects.create(
                    transaction_type=transaction_type,
                    category=category,
                    date=transaction_date.date(),
                    title=title,
                    total=round(amount, 2),
                    owner_id=self.test_username,
                    account_id=account_id
                )
                
            else:  # 20% transfer
                # Transfer transaction
                transaction_type = "Transfer"
                category = random.choice(self.transfer_categories)
                
                # Choose two different accounts for transfer
                from_account = random.choice(accounts)
                to_account = random.choice([acc for acc in accounts if acc.id != from_account.id])
                
                amount = random.uniform(50, 1000)  # Transfer amounts
                title = f"Transfer to {to_account.account_name}"
                
                # Create transfer transaction
                transaction = Transaction.objects.create(
                    transaction_type=transaction_type,
                    category=category,
                    date=transaction_date.date(),
                    title=title,
                    total=round(amount, 2),
                    owner_id=self.test_username,
                    from_account_id=str(from_account.id),
                    to_account_id=str(to_account.id)
                )
            
            transactions_created.append(transaction)
            
            if (i + 1) % 20 == 0:
                print(f"  ✅ Created {i + 1} transactions...")
        
        print(f"  ✅ Created {len(transactions_created)} total transactions")
        return transactions_created
    
    def update_account_balances(self, accounts, transactions):
        """Update account balances based on transactions."""
        print(f"\n🔄 Updating account balances...")
        
        for account in accounts:
            # Get all transactions that affect this account
            account_transactions = []
            for t in transactions:
                if (t.account_id == str(account.id) or  # Regular income/expense
                    t.from_account_id == str(account.id) or  # Transfer from this account
                    t.to_account_id == str(account.id)):  # Transfer to this account
                    account_transactions.append(t)
            
            # Start with the original balance
            current_balance = account.total
            
            # Apply all transactions
            for transaction in account_transactions:
                if transaction.transaction_type == "Income":
                    current_balance += transaction.total
                elif transaction.transaction_type == "Expense":
                    current_balance -= transaction.total
                elif transaction.transaction_type == "Transfer":
                    # For transfers, check if this account is source or destination
                    if transaction.from_account_id == str(account.id):
                        # This account is the source - money goes out
                        current_balance -= transaction.total
                    elif transaction.to_account_id == str(account.id):
                        # This account is the destination - money comes in
                        current_balance += transaction.total
            
            # Update the account balance
            account.total = round(current_balance, 2)
            account.save()
            
            print(f"  ✅ {account.account_name}: ${account.total:,.2f}")
    
    def generate_summary_report(self, accounts, transactions):
        """Generate a summary report of the created data."""
        print(f"\n📊 TEST DATA SUMMARY REPORT")
        print("=" * 50)
        
        print(f"\n👤 User: {self.user.username}")
        print(f"📅 Data Period: Last 365 days")
        print(f"🏦 Accounts Created: {len(accounts)}")
        print(f"💰 Transactions Created: {len(transactions)}")
        
        # Account summary
        print(f"\n🏦 ACCOUNT SUMMARY:")
        total_balance = 0
        for account in accounts:
            print(f"  • {account.account_name}: ${account.total:,.2f}")
            total_balance += account.total
        print(f"  💰 Total Balance: ${total_balance:,.2f}")
        
        # Transaction summary
        income_transactions = [t for t in transactions if t.transaction_type == "Income"]
        expense_transactions = [t for t in transactions if t.transaction_type == "Expense"]
        
        total_income = sum(t.total for t in income_transactions)
        total_expenses = sum(t.total for t in expense_transactions)
        
        print(f"\n💰 TRANSACTION SUMMARY:")
        print(f"  📈 Total Income: ${total_income:,.2f} ({len(income_transactions)} transactions)")
        print(f"  📉 Total Expenses: ${total_expenses:,.2f} ({len(expense_transactions)} transactions)")
        print(f"  💵 Net: ${total_income - total_expenses:,.2f}")
        
        # Top categories
        expense_categories = {}
        for transaction in expense_transactions:
            category = transaction.category
            expense_categories[category] = expense_categories.get(category, 0) + transaction.total
        
        print(f"\n📊 TOP EXPENSE CATEGORIES:")
        sorted_categories = sorted(expense_categories.items(), key=lambda x: x[1], reverse=True)
        for category, amount in sorted_categories[:5]:
            print(f"  • {category}: ${amount:,.2f}")
        
        print(f"\n✅ Test data generation completed successfully!")
        print(f"🌐 You can now test the application with realistic data.")
    
    def run(self):
        """Main method to run the test data generation."""
        print("🚀 Starting test data generation for Home Money Management API")
        print("=" * 60)
        
        # Check if test user exists
        if not self.get_or_create_test_user():
            return False
        
        try:
            # Create accounts (one of each type: Débito, Crédito, Efectivo)
            accounts = self.create_accounts(num_accounts=3)
            
            # Create transactions
            transactions = self.create_transactions(accounts, num_transactions=100)
            
            # Update account balances
            self.update_account_balances(accounts, transactions)
            
            # Generate summary report
            self.generate_summary_report(accounts, transactions)
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating test data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    generator = TestDataGenerator()
    success = generator.run()
    
    if success:
        print(f"\n🎉 Test data generation completed successfully!")
        print(f"🔗 You can now access the application at: http://localhost:8080")
        print(f"👤 Login with: testUser / testpass123")
    else:
        print(f"\n❌ Test data generation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
