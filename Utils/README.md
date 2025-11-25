# Utils Directory

This directory contains utility scripts and tools for the Home Money Management project.

## Structure

```text
Utils/
├── README.md                    # This file
└── TestData/                    # Test data generation scripts
    ├── create_docker_test_data.py    # Docker-specific test data script
    ├── populate_test_data.bat        # Windows batch script for test data
    ├── populate_test_data.sh         # Unix/Linux shell script for test data
    ├── populate_test_data.py         # Full test data generator (4 accounts, 100 transactions)
    └── populate_quick_test_data.py   # Quick test data generator (2 accounts, 20 transactions)
```

## Test Data Generation Scripts

### Quick Start

**Windows:**

```bash
cd Utils/TestData
populate_test_data.bat
```

**Unix/Linux:**

```bash
cd Utils/TestData
chmod +x populate_test_data.sh
./populate_test_data.sh
```

### Available Scripts

1. **`populate_quick_test_data.py`** - Creates minimal test data (2 accounts, 20 transactions)
   - Quick setup for basic testing
   - 2 accounts: Checking and Savings
   - 20 transactions over the last 30 days

2. **`populate_test_data.py`** - Creates comprehensive test data (4 accounts, 100 transactions)
   - Full test dataset
   - 4 accounts: Checking, Savings, Credit Card, Investment
   - 100 transactions over the last 365 days
   - Realistic transaction patterns and amounts

3. **`create_docker_test_data.py`** - Docker-specific script for containerized environments
   - Designed for use within Docker containers
   - Handles container-specific paths and configurations

4. **`populate_test_data.bat`** - Windows interactive menu script
   - Menu-driven interface
   - Choose between quick or full data generation

5. **`populate_test_data.sh`** - Unix/Linux interactive menu script
   - Menu-driven interface
   - Choose between quick or full data generation

### Prerequisites

Before running any test data scripts:

1. **Django environment must be set up**
2. **`testUser` must exist** in the database
3. **Database migrations must be applied**

### Create Test User

If `testUser` doesn't exist:

```bash
cd API
python create_test_user.py
```

**Test User Credentials:**

- Username: `testUser`
- Password: `testpass123`

### Usage Examples

#### Option 1: Using Interactive Scripts (Recommended)

```bash
# Windows
cd Utils/TestData
populate_test_data.bat

# Unix/Linux
cd Utils/TestData
chmod +x populate_test_data.sh
./populate_test_data.sh
```

#### Option 2: Direct Python Execution

```bash
cd API

# Quick test data (2 accounts, 20 transactions)
python ../Utils/TestData/populate_quick_test_data.py

# Full test data (4 accounts, 100 transactions)
python ../Utils/TestData/populate_test_data.py
```

### Generated Data Details

#### Accounts Created

- **Checking Account**: Chase Bank, ~$2,500 balance
- **Savings Account**: Bank of America, ~$15,000 balance
- **Credit Card**: Various banks, negative balance
- **Investment Account**: Various banks, higher balance

#### Transaction Categories

- **Income**: Salary, Freelance, Investment Returns, Rental Income, Bonus
- **Expenses**: Groceries, Restaurants, Transportation, Gas, Utilities, Rent/Mortgage, Insurance, Healthcare, Entertainment, Shopping, Travel, Education, Phone, Internet, Gym, Coffee, Subscriptions, Home Improvement, Car Maintenance

#### Realistic Data Features

- **Realistic amounts** based on category (e.g., $5-50 for coffee, $800-3000 for rent)
- **Realistic transaction titles** (e.g., "Starbucks", "Whole Foods", "Shell Gas Station")
- **Proper date distribution** over the specified time period
- **Account balance updates** based on transaction history
- **70% expenses, 30% income** ratio for realistic patterns

### Customization

#### Modify Data Volume

Edit the script parameters:

```python
# In populate_test_data.py
accounts = self.create_accounts(num_accounts=4)  # Change number of accounts
transactions = self.create_transactions(accounts, num_transactions=100)  # Change number of transactions
```

#### Add Custom Categories

Add to the data pools in `TestDataGenerator.__init__()`:

```python
self.expense_categories.append("Custom Category")
self.transaction_titles["Custom Category"] = ["Custom Title 1", "Custom Title 2"]
```

#### Modify Date Range

```python
# In populate_test_data.py
start_date = datetime.now() - timedelta(days=365)  # Change to desired range

# In populate_quick_test_data.py
start_date = datetime.now() - timedelta(days=30)  # Change to desired range
```

### Cleanup

#### Clear All Test Data

```python
# Clear accounts
Account.objects.filter(owner="testUser").delete()

# Clear transactions
Transaction.objects.filter(owner_id="testUser").delete()
```

#### Clear Specific Data

```python
# Clear specific account
Account.objects.filter(owner="testUser", account_name="Chase Checking").delete()

# Clear transactions by category
Transaction.objects.filter(owner_id="testUser", category="Groceries").delete()
```

### Troubleshooting

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

### Notes

- **Data is realistic** but randomly generated
- **Account balances** are automatically calculated based on transactions
- **Existing data** is cleared before creating new data
- **Scripts are idempotent** - can be run multiple times safely
- **All data** is associated with the "testUser" account
