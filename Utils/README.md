# Utils Directory

This directory contains utility scripts and tools for the Home Money Management project.

## Structure

```
Utils/
├── README.md                    # This file
└── TestData/                    # Test data generation scripts
    ├── create_docker_test_data.py    # Docker-specific test data script
    ├── populate_test_data.bat        # Windows batch script for test data
    ├── populate_test_data.sh         # Unix/Linux shell script for test data
    ├── populate_test_data.py         # Full test data generator (4 accounts, 100 transactions)
    └── populate_quick_test_data.py   # Quick test data generator (2 accounts, 20 transactions)
```

## Test Data Scripts

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

### Individual Scripts

1. **`populate_quick_test_data.py`** - Creates minimal test data (2 accounts, 20 transactions)
2. **`populate_test_data.py`** - Creates comprehensive test data (4 accounts, 100 transactions)
3. **`create_docker_test_data.py`** - Docker-specific script for containerized environments
4. **`populate_test_data.bat`** - Windows interactive menu script
5. **`populate_test_data.sh`** - Unix/Linux interactive menu script

### Usage

All scripts are designed to work with the `testUser` account. Make sure the test user exists before running any data generation scripts.

**Prerequisites:**

- Django environment set up
- `testUser` created in the database
- For Docker: containers running

**Login Credentials:**

- Username: `testUser`
- Password: `testpass123`

For detailed information about test data generation, see the main project documentation.
