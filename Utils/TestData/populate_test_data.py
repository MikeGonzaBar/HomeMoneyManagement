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
        
        self.account_types = ["Checking", "Savings", "Credit Card", "Investment", "Business"]
        
        self.income_categories = [
            "Salary", "Freelance", "Investment Returns", "Rental Income", 
            "Bonus", "Commission", "Side Business", "Dividends", "Interest"
        ]
        
        self.expense_categories = [
            "Groceries", "Restaurants", "Transportation", "Gas", "Utilities",
            "Rent/Mortgage", "Insurance", "Healthcare", "Entertainment",
            "Shopping", "Travel", "Education", "Phone", "Internet", "Gym",
            "Coffee", "Subscriptions", "Home Improvement", "Car Maintenance"
        ]
        
        self.transaction_titles = {
            "Groceries": [
                "Whole Foods", "Kroger", "Safeway", "Trader Joe's", "Costco",
                "Walmart", "Target", "Local Market", "Organic Store"
            ],
            "Restaurants": [
                "McDonald's", "Starbucks", "Pizza Hut", "Subway", "Chipotle",
                "Local Diner", "Fine Dining", "Food Truck", "Coffee Shop"
            ],
            "Transportation": [
                "Uber", "Lyft", "Taxi", "Bus Pass", "Train Ticket",
                "Parking Fee", "Toll Road", "Car Rental"
            ],
            "Gas": [
                "Shell", "Exxon", "BP", "Chevron", "7-Eleven Gas",
                "Costco Gas", "Local Station"
            ],
            "Utilities": [
                "Electric Bill", "Water Bill", "Gas Bill", "Internet Bill",
                "Cable Bill", "Trash Service", "Sewer Bill"
            ],
            "Rent/Mortgage": [
                "Monthly Rent", "Mortgage Payment", "HOA Fee", "Property Tax"
            ],
            "Insurance": [
                "Car Insurance", "Health Insurance", "Home Insurance",
                "Life Insurance", "Renters Insurance"
            ],
            "Healthcare": [
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
            "Travel": [
                "Flight Ticket", "Hotel Booking", "Airbnb", "Car Rental",
                "Travel Insurance", "Vacation Package", "Cruise"
            ],
            "Education": [
                "Tuition", "Textbooks", "Online Course", "Certification",
                "Workshop", "Conference", "Training"
            ],
            "Phone": [
                "Verizon", "AT&T", "T-Mobile", "Sprint", "Google Fi"
            ],
            "Internet": [
                "Comcast", "Verizon Fios", "AT&T Internet", "Spectrum",
                "Cox", "CenturyLink"
            ],
            "Gym": [
                "Planet Fitness", "LA Fitness", "24 Hour Fitness", "Gold's Gym",
                "Local Gym", "Yoga Studio", "Personal Trainer"
            ],
            "Coffee": [
                "Starbucks", "Dunkin'", "Local Coffee Shop", "Peet's Coffee",
                "Caribou Coffee", "Tim Hortons"
            ],
            "Subscriptions": [
                "Adobe Creative", "Microsoft Office", "Dropbox", "iCloud",
                "Google Drive", "Slack", "Zoom", "Canva"
            ],
            "Home Improvement": [
                "Home Depot", "Lowe's", "IKEA", "Hardware Store",
                "Paint Store", "Furniture Store", "Garden Center"
            ],
            "Car Maintenance": [
                "Oil Change", "Tire Rotation", "Brake Service", "Car Wash",
                "Auto Repair", "DMV Fee", "Registration"
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
        
        for i in range(num_accounts):
            account_type = random.choice(self.account_types)
            bank = random.choice(self.banks)
            
            # Generate realistic account names
            if account_type == "Checking":
                account_name = f"{bank} Checking"
                base_balance = random.uniform(500, 5000)
            elif account_type == "Savings":
                account_name = f"{bank} Savings"
                base_balance = random.uniform(1000, 25000)
            elif account_type == "Credit Card":
                account_name = f"{bank} Credit Card"
                base_balance = random.uniform(-5000, -500)  # Negative for credit card
            elif account_type == "Investment":
                account_name = f"{bank} Investment"
                base_balance = random.uniform(10000, 100000)
            else:  # Business
                account_name = f"{bank} Business"
                base_balance = random.uniform(1000, 10000)
            
            account = Account.objects.create(
                account_type=account_type,
                bank=bank,
                total=round(base_balance, 2),
                account_name=account_name,
                owner=self.test_username
            )
            
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
            
            # 70% chance of expense, 30% chance of income
            if random.random() < 0.7:
                transaction_type = "Expense"
                category = random.choice(self.expense_categories)
                
                # Generate realistic expense amounts based on category
                if category in ["Groceries"]:
                    amount = random.uniform(20, 200)
                elif category in ["Restaurants", "Coffee"]:
                    amount = random.uniform(5, 50)
                elif category in ["Gas"]:
                    amount = random.uniform(30, 80)
                elif category in ["Utilities"]:
                    amount = random.uniform(50, 300)
                elif category in ["Rent/Mortgage"]:
                    amount = random.uniform(800, 3000)
                elif category in ["Insurance"]:
                    amount = random.uniform(100, 500)
                elif category in ["Healthcare"]:
                    amount = random.uniform(50, 500)
                elif category in ["Entertainment"]:
                    amount = random.uniform(10, 100)
                elif category in ["Shopping"]:
                    amount = random.uniform(20, 500)
                elif category in ["Travel"]:
                    amount = random.uniform(100, 2000)
                else:
                    amount = random.uniform(10, 200)
                
                # Generate title based on category
                if category in self.transaction_titles:
                    title = random.choice(self.transaction_titles[category])
                else:
                    title = f"{category} Payment"
                
            else:
                transaction_type = "Income"
                category = random.choice(self.income_categories)
                
                # Generate realistic income amounts
                if category == "Salary":
                    amount = random.uniform(2000, 8000)
                elif category == "Freelance":
                    amount = random.uniform(200, 2000)
                elif category == "Investment Returns":
                    amount = random.uniform(50, 1000)
                elif category == "Rental Income":
                    amount = random.uniform(800, 2500)
                elif category == "Bonus":
                    amount = random.uniform(500, 5000)
                else:
                    amount = random.uniform(100, 1000)
                
                title = f"{category} Payment"
            
            transaction = Transaction.objects.create(
                transaction_type=transaction_type,
                category=category,
                date=transaction_date.date(),
                title=title,
                total=round(amount, 2),
                owner_id=self.test_username,
                account_id=account_id
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
            account_transactions = [t for t in transactions if t.account_id == str(account.id)]
            
            # Start with the original balance
            current_balance = account.total
            
            # Apply all transactions
            for transaction in account_transactions:
                if transaction.transaction_type == "Income":
                    current_balance += transaction.total
                else:  # Expense
                    current_balance -= transaction.total
            
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
            # Create accounts
            accounts = self.create_accounts(num_accounts=4)
            
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
