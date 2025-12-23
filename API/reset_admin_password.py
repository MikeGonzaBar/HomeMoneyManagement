#!/usr/bin/env python
"""
Script to reset Django admin password or create a new superuser.
This script helps when you've forgotten your admin credentials.
"""

import os
import sys
import django
from django.contrib.auth import get_user_model

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneyManagement.settings')
django.setup()

def list_superusers():
    """List all existing superusers."""
    User = get_user_model()
    
    # Try to filter by is_superuser if the field exists
    try:
        if hasattr(User, 'is_superuser'):
            superusers = User.objects.filter(is_superuser=True)
        else:
            # If no is_superuser field, list all users
            superusers = User.objects.all()
    except:
        # Fallback: list all users
        superusers = User.objects.all()
    
    if superusers.exists():
        print("\n=== Existing Users ===")
        for user in superusers:
            is_super = getattr(user, 'is_superuser', None)
            super_status = " (Superuser)" if is_super else ""
            print(f"  - Username: {user.username}{super_status}")
            print(f"    Email: {getattr(user, 'email', 'N/A')}")
            print(f"    Name: {user.first_name} {user.last_name}")
            print()
        return superusers
    else:
        print("\nNo users found in the database.")
        return None

def reset_password(username, new_password):
    """Reset password for an existing user."""
    User = get_user_model()
    
    try:
        # Try to get user (with or without superuser check)
        if hasattr(User, 'is_superuser'):
            user = User.objects.get(username=username, is_superuser=True)
        else:
            user = User.objects.get(username=username)
        
        user.set_password(new_password)
        user.save()
        print(f"\n✓ Password reset successfully for user '{username}'!")
        print(f"  New password: {new_password}")
        return True
    except User.DoesNotExist:
        print(f"\n✗ Error: User '{username}' not found.")
        return False
    except Exception as e:
        print(f"\n✗ Error resetting password: {e}")
        return False

def create_new_superuser(username, email, password):
    """Create a new superuser."""
    User = get_user_model()
    
    # Check if username already exists
    if User.objects.filter(username=username).exists():
        print(f"\n✗ Error: Username '{username}' already exists.")
        print("  Use 'reset' option to change password instead.")
        return False
    
    try:
        superuser = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name="Admin",
            last_name="User"
        )
        print(f"\n✓ Superuser '{username}' created successfully!")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        return True
    except Exception as e:
        print(f"\n✗ Error creating superuser: {e}")
        return False

def main():
    """Main function to handle password reset or superuser creation."""
    print("=" * 50)
    print("Django Admin Password Reset Tool")
    print("=" * 50)
    
    # List existing superusers
    superusers = list_superusers()
    
    print("\nWhat would you like to do?")
    print("1. Reset password for existing superuser")
    print("2. Create new superuser")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        if not superusers:
            print("\nNo users found. Please create one first.")
            return
        
        print("\nAvailable users:")
        usernames = [user.username for user in superusers]
        for i, username in enumerate(usernames, 1):
            print(f"  {i}. {username}")
        
        username_input = input("\nEnter username to reset password: ").strip()
        
        if username_input not in usernames:
            print(f"\n✗ Error: '{username_input}' is not a valid user.")
            return
        
        new_password = input("Enter new password: ").strip()
        if not new_password:
            print("\n✗ Error: Password cannot be empty.")
            return
        
        confirm_password = input("Confirm new password: ").strip()
        if new_password != confirm_password:
            print("\n✗ Error: Passwords do not match.")
            return
        
        reset_password(username_input, new_password)
        
    elif choice == "2":
        username = input("Enter new admin username: ").strip()
        if not username:
            print("\n✗ Error: Username cannot be empty.")
            return
        
        email = input("Enter email (optional): ").strip() or "admin@example.com"
        password = input("Enter password: ").strip()
        if not password:
            print("\n✗ Error: Password cannot be empty.")
            return
        
        confirm_password = input("Confirm password: ").strip()
        if password != confirm_password:
            print("\n✗ Error: Passwords do not match.")
            return
        
        create_new_superuser(username, email, password)
        
    elif choice == "3":
        print("\nExiting...")
        return
    else:
        print("\n✗ Invalid choice. Please enter 1, 2, or 3.")
        return
    
    print("\n" + "=" * 50)
    print("You can now access the admin interface at: http://localhost:8000/admin/")
    print("=" * 50)

if __name__ == "__main__":
    main()

