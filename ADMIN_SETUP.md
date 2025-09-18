# Django Admin Interface Setup

This document explains how to access and use the Django admin interface for your Home Money Management API.

## Overview

The Django admin interface has been configured to provide a web-based interface for managing all your models and their data. You can view, create, edit, and delete records for:

- **Users**: User accounts and authentication data
- **Accounts**: Financial accounts with balances and ownership
- **Transactions**: Financial transactions with categories and dates

## Accessing the Admin Interface

### 1. Start the Application

```bash
docker-compose up --build
```

### 2. Access the Admin Interface

Once the containers are running, navigate to:

```text
http://localhost:8000/admin/
```

### 3. Login Credentials

The superuser creation script will run automatically when you start the containers with default credentials:

- Username: `admin`
- Email: `admin@example.com`  
- Password: `admin123`

## Admin Interface Features

### User Management

- **List View**: Shows all users with ID, username, first name, last name, and password
- **Search**: Search by username, first name, or last name
- **Filters**: Filter by first name or last name
- **Fieldsets**: Organized into "User Information" and "Personal Information" sections

### Account Management

- **List View**: Shows all accounts with ID, account name, type, bank, total, and owner
- **Search**: Search by account name, owner, or bank
- **Filters**: Filter by account type, bank, or owner
- **Fieldsets**: Organized into "Account Information", "Financial Information", and "Ownership" sections

### Transaction Management

- **List View**: Shows all transactions with ID, title, type, category, total, date, owner, and account
- **Search**: Search by title, owner ID, or account ID
- **Filters**: Filter by transaction type, category, date, owner, or account
- **Date Hierarchy**: Navigate transactions by year and month
- **Fieldsets**: Organized into "Transaction Details", "Date Information", and "Ownership & Account" sections

## Manual Superuser Creation

If you need to create a superuser manually:

### Option 1: Using the provided script

```bash
# Make the script executable
chmod +x create_admin_user.sh

# Run the script
./create_admin_user.sh
```

### Option 2: Using Docker directly (interactive)

```bash
docker-compose exec money-management-api python /HomeMoneyManagement/create_superuser_interactive.py
```

### Option 2b: Using Docker directly (non-interactive with defaults)

```bash
docker-compose exec money-management-api python /HomeMoneyManagement/create_superuser.py
```

### Option 3: Using Django management command

```bash
docker-compose exec money-management-api python /HomeMoneyManagement/manage.py createsuperuser
```

## Security Notes

- The default credentials (admin/admin123) are for development only
- Change the password immediately in production
- Consider using environment variables for sensitive data
- The admin interface is only accessible when DEBUG=True (development mode)

## Troubleshooting

### Admin interface not accessible

1. Ensure the containers are running: `docker-compose ps`
2. Check the logs: `docker-compose logs money-management-api`
3. Verify the port mapping: `docker-compose port money-management-api 8000`

### Superuser creation fails

1. Check if a superuser already exists
2. Ensure the database migrations have been applied
3. Check the Django logs for error messages

### Models not showing in admin

1. Verify the models are registered in their respective `admin.py` files
2. Check that the apps are included in `INSTALLED_APPS` in `settings.py`
3. Restart the containers after making changes

## File Structure

```text
API/
├── users/admin.py          # User model admin configuration
├── account/admin.py        # Account model admin configuration  
├── transaction/admin.py    # Transaction model admin configuration
├── create_superuser.py     # Script to create admin user
└── MoneyManagement/
    └── settings.py         # Django settings with admin app enabled
```

## Next Steps

1. Start the application with `docker-compose up --build`
2. Access the admin interface at `http://localhost:8000/admin/`
3. Create your admin user when prompted
4. Explore and manage your data through the web interface
