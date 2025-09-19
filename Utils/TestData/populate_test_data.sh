#!/bin/bash

echo "========================================"
echo "Home Money Management - Test Data Setup"
echo "========================================"
echo

echo "Checking if testUser exists..."
cd ../../API
python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneyManagement.settings')
django.setup()
from users.models import User
if User.objects.filter(username='testUser').exists():
    print('✅ testUser exists')
else:
    print('❌ testUser not found')
"

echo
echo "Choose test data option:"
echo "1. Quick test data (2 accounts, 20 transactions)"
echo "2. Full test data (4 accounts, 100 transactions)"
echo "3. Exit"
echo

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo
        echo "Creating quick test data..."
        cd ../../Utils/TestData
        python3 populate_quick_test_data.py
        ;;
    2)
        echo
        echo "Creating full test data..."
        cd ../../Utils/TestData
        python3 populate_test_data.py
        ;;
    3)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo
echo "========================================"
echo "Test data setup completed!"
echo "========================================"
echo
echo "You can now:"
echo "1. Start the application: docker-compose up --build"
echo "2. Access frontend: http://localhost:8080"
echo "3. Login with: testUser / testpass123"
echo
