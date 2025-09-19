# Test Data Generation Scripts

> **Note**: The test data scripts have been moved to the `Utils/TestData/` directory for better organization. This file is kept for reference.

**New Location**: [Utils/TestData/](../Utils/TestData/)

This directory contains scripts to populate the database with realistic test data for the Home Money Management application.

## 📁 Available Scripts

### 1. `populate_test_data.py` - Full Test Data Generator

- **Purpose**: Creates comprehensive test data with realistic patterns
- **Data Created**:
  - 4 different accounts (Checking, Savings, Credit Card, Investment)
  - 100 transactions over the last 365 days
  - Realistic transaction amounts and categories
  - Proper account balance calculations

### 2. `populate_quick_test_data.py` - Quick Test Data Generator

- **Purpose**: Creates minimal test data for quick testing
- **Data Created**:
  - 2 accounts (Checking, Savings)
  - 20 transactions over the last 30 days
  - Predefined realistic transactions

### 3. `populate_test_data.bat` - Windows Batch Script

- **Purpose**: Interactive script for Windows users
- **Features**: Menu-driven interface to choose between quick or full data

### 4. `populate_test_data.sh` - Unix/Linux Shell Script

- **Purpose**: Interactive script for Unix/Linux users
- **Features**: Menu-driven interface to choose between quick or full data

## 🚀 Quick Start

### Prerequisites

1. **testUser must exist** in the database
2. **Django environment** must be set up
3. **Database migrations** must be applied

### Create testUser (if not exists)

```bash
cd API
python create_test_user.py
```

### Run Test Data Generation

#### Option 1: Using Batch Scripts (Recommended)

```bash
# Windows
populate_test_data.bat

# Unix/Linux
./populate_test_data.sh
```

#### Option 2: Direct Python Execution

```bash
cd API

# Quick test data (2 accounts, 20 transactions)
python populate_quick_test_data.py

# Full test data (4 accounts, 100 transactions)
python populate_test_data.py
```

## 📊 Generated Data Details

### Accounts Created

- **Checking Account**: Chase Bank, ~$2,500 balance
- **Savings Account**: Bank of America, ~$15,000 balance
- **Credit Card**: Various banks, negative balance
- **Investment Account**: Various banks, higher balance

### Transaction Categories

- **Income**: Salary, Freelance, Investment Returns, Rental Income, Bonus
- **Expenses**: Groceries, Restaurants, Transportation, Gas, Utilities, Rent/Mortgage, Insurance, Healthcare, Entertainment, Shopping, Travel, Education, Phone, Internet, Gym, Coffee, Subscriptions, Home Improvement, Car Maintenance

### Realistic Data Features

- **Realistic amounts** based on category (e.g., $5-50 for coffee, $800-3000 for rent)
- **Realistic transaction titles** (e.g., "Starbucks", "Whole Foods", "Shell Gas Station")
- **Proper date distribution** over the specified time period
- **Account balance updates** based on transaction history
- **70% expenses, 30% income** ratio for realistic patterns

## 🔧 Customization

### Modify Data Volume

Edit the script parameters:

```python
# In populate_test_data.py
accounts = self.create_accounts(num_accounts=4)  # Change number of accounts
transactions = self.create_transactions(accounts, num_transactions=100)  # Change number of transactions
```

### Add Custom Categories

Add to the data pools in `TestDataGenerator.__init__()`:

```python
self.expense_categories.append("Custom Category")
self.transaction_titles["Custom Category"] = ["Custom Title 1", "Custom Title 2"]
```

### Modify Date Range

```python
# In populate_test_data.py
start_date = datetime.now() - timedelta(days=365)  # Change to desired range

# In populate_quick_test_data.py
start_date = datetime.now() - timedelta(days=30)  # Change to desired range
```

## 🧹 Cleanup

### Clear All Test Data

```python
# Clear accounts
Account.objects.filter(owner="testUser").delete()

# Clear transactions
Transaction.objects.filter(owner_id="testUser").delete()
```

### Clear Specific Data

```python
# Clear specific account
Account.objects.filter(owner="testUser", account_name="Chase Checking").delete()

# Clear transactions by category
Transaction.objects.filter(owner_id="testUser", category="Groceries").delete()
```

## 📈 Usage Examples

### After Running Scripts

1. **Start the application**: `docker-compose up --build`
2. **Access frontend**: <http://localhost:8080>
3. **Login**: testUser / testpass123
4. **View data**: Navigate through accounts, transactions, and analytics

### Testing Scenarios

- **Account Management**: Create, edit, delete accounts
- **Transaction Management**: Add, edit, delete transactions
- **Data Visualization**: View pie charts, projections, and analytics
- **Date Filtering**: Filter transactions by month/year
- **Category Analysis**: View spending by category

## 🐛 Troubleshooting

### Common Issues

#### "testUser not found"

```bash
cd API
python create_test_user.py
```

#### "Django not configured"

```bash
cd API
python -c "import django; django.setup()"
```

#### "Database connection error"

```bash
cd API
python manage.py migrate
```

#### "Permission denied" (Unix/Linux)

```bash
chmod +x populate_test_data.sh
```

### Debug Mode

Add debug prints to scripts:

```python
print(f"Debug: Creating transaction {i+1}/{num_transactions}")
print(f"Debug: Account balance: {account.total}")
```

## 📝 Notes

- **Data is realistic** but randomly generated
- **Account balances** are automatically calculated based on transactions
- **Existing data** is cleared before creating new data
- **Scripts are idempotent** - can be run multiple times safely
- **All data** is associated with the "testUser" account

## 🎯 Next Steps

After generating test data:

1. Test all application features
2. Verify data visualization works correctly
3. Test filtering and search functionality
4. Validate account balance calculations
5. Test transaction CRUD operations

---

**Happy Testing!** 🚀
