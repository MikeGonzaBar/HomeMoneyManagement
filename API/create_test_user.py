#!/usr/bin/env python
"""
Script to create a test user for debugging login issues.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneyManagement.settings')
django.setup()

from users.models import User

def create_test_user():
    """Create a test user for debugging."""
    username = 'testUser'
    password = 'testpass123'
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists!")
        user = User.objects.get(username=username)
        print(f"  - ID: {user.id}")
        print(f"  - First Name: {user.first_name}")
        print(f"  - Last Name: {user.last_name}")
        
        # Test password
        if user.check_password(password):
            print(f"  - Password verification: ✅ SUCCESS")
        else:
            print(f"  - Password verification: ❌ FAILED")
            print("  - Updating password...")
            user.set_password(password)
            user.save()
            print("  - Password updated successfully!")
    else:
        print(f"Creating new user '{username}'...")
        user = User(
            username=username,
            first_name='Test',
            last_name='User'
        )
        user.set_password(password)
        user.save()
        print(f"✅ User created successfully!")
        print(f"  - ID: {user.id}")
        print(f"  - Username: {user.username}")
        print(f"  - First Name: {user.first_name}")
        print(f"  - Last Name: {user.last_name}")
    
    # List all users
    print("\nAll users in database:")
    for u in User.objects.all():
        print(f"  - {u.username} (ID: {u.id}) - {u.first_name} {u.last_name}")

if __name__ == '__main__':
    create_test_user()
