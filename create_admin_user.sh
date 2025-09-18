#!/bin/bash

# Script to create Django admin superuser
# This script can be run manually if you need to create an admin user

echo "Creating Django admin superuser..."
echo "This will create an admin user for accessing the Django admin interface."
echo ""

# Run the interactive superuser creation script
docker-compose exec money-management-api python /HomeMoneyManagement/create_superuser_interactive.py

echo ""
echo "Admin interface will be available at: http://localhost:8000/admin/"
echo "Use the credentials you just created to log in."
