#!/usr/bin/env python
"""
Interactive script to create a Django superuser for admin access.
This version prompts for user input and should be run manually.
"""

import os
import sys
import django
from django.contrib.auth import get_user_model

# Add the project directory to Python path
sys.path.append('/HomeMoneyManagement')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneyManagement.settings')
django.setup()

def create_superuser():
    """Create a superuser for Django admin access."""
    User = get_user_model()
    
    # Check if superuser already exists
    if User.objects.filter(is_superuser=True).exists():
        print("Superuser already exists!")
        return
    
    # Create superuser with user input
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email (default: admin@example.com): ").strip() or "admin@example.com"
    password = input("Enter admin password (default: admin123): ").strip() or "admin123"
    
    try:
        superuser = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name="Admin",
            last_name="User"
        )
        print(f"Superuser '{username}' created successfully!")
        print(f"You can now access the admin interface at: http://localhost:8000/admin/")
        print(f"Username: {username}")
        print(f"Password: {password}")
    except Exception as e:
        print(f"Error creating superuser: {e}")

if __name__ == "__main__":
    create_superuser()
