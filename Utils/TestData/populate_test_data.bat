@echo off
echo ========================================
echo Home Money Management - Test Data Setup
echo ========================================
echo.

echo Checking if testUser exists...
cd ..\..\API
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneyManagement.settings'); django.setup(); from users.models import User; print('✅ testUser exists' if User.objects.filter(username='testUser').exists() else '❌ testUser not found')"

echo.
echo Choose test data option:
echo 1. Quick test data (2 accounts, 20 transactions)
echo 2. Full test data (4 accounts, 100 transactions)
echo 3. Exit
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Creating quick test data...
    cd ..\..\Utils\TestData
    python populate_quick_test_data.py
) else if "%choice%"=="2" (
    echo.
    echo Creating full test data...
    cd ..\..\Utils\TestData
    python populate_test_data.py
) else if "%choice%"=="3" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice. Please run the script again.
    exit /b 1
)

echo.
echo ========================================
echo Test data setup completed!
echo ========================================
echo.
echo You can now:
echo 1. Start the application: docker-compose up --build
echo 2. Access frontend: http://localhost:8080
echo 3. Login with: testUser / testpass123
echo.
pause
