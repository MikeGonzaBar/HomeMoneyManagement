"""
User services module for handling business logic related to user operations.
This module separates business logic from models and views for better maintainability.
"""

from typing import Dict, List, Optional
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import User


class UserService:
    """Service class for user-related business logic."""
    
    @staticmethod
    def validate_user_data(data: Dict) -> List[str]:
        """
        Validates user data and returns list of missing or invalid fields.
        
        Args:
            data (Dict): User data dictionary
            
        Returns:
            List[str]: List of missing or invalid field names
        """
        required_fields = ["username", "password", "first_name", "last_name"]
        missing_fields = []
        
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        return missing_fields
    
    @staticmethod
    def create_user(data: Dict) -> Dict:
        """
        Creates a new user with proper validation and error handling.
        
        Args:
            data (Dict): User data dictionary
            
        Returns:
            Dict: Response dictionary with success/error information
        """
        # Validate input data
        missing_fields = UserService.validate_user_data(data)
        if missing_fields:
            return {
                "error": "Invalid data",
                "missing_fields": missing_fields,
                "message": "Please provide all required fields with valid values"
            }
        
        # Check if username already exists
        if User.objects.filter(username=data["username"]).exists():
            return {
                "error": "Username already exists",
                "message": "A user with this username already exists"
            }
        
        try:
            # Create user with hashed password
            user = User(
                username=data["username"],
                first_name=data["first_name"],
                last_name=data["last_name"]
            )
            user.set_password(data["password"])  # Hash the password
            user.save()
            
            return {
                "success": True,
                "message": "User created successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            }
            
        except IntegrityError as e:
            return {
                "error": "Database error",
                "message": "Failed to create user due to database constraint violation"
            }
        except Exception as e:
            return {
                "error": "Unexpected error",
                "message": "An unexpected error occurred while creating user"
            }
    
    @staticmethod
    def authenticate_user(username_or_email: str, password: str) -> Dict:
        """
        Authenticates a user with username/email and password.
        
        Args:
            username_or_email (str): Username or email
            password (str): Plain text password
            
        Returns:
            Dict: Authentication result with user data or error
        """
        try:
            # Try to find user by username
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                user = None
            
            if not user:
                return {
                    "error": "Invalid credentials",
                    "message": "User not found"
                }
            
            # Check password
            if user.check_password(password):
                return {
                    "success": True,
                    "message": "Authentication successful",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    }
                }
            else:
                return {
                    "error": "Invalid credentials",
                    "message": "Incorrect password"
                }
                
        except Exception as e:
            return {
                "error": "Authentication error",
                "message": "An error occurred during authentication"
            }
    
    @staticmethod
    def delete_user(username: str, password: str) -> Dict:
        """
        Deletes a user after verifying their password.
        Also deletes all related accounts, transactions, and bank statements.
        
        Args:
            username (str): Username of user to delete
            password (str): User's password for verification
            
        Returns:
            Dict: Deletion result
        """
        try:
            user = User.objects.get(username=username)
            
            # Verify password before deletion
            if user.check_password(password):
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
                
                # Cascade delete related objects
                from account.models import Account
                from transaction.models import Transaction
                from bankstatements.models import BankStatement
                
                user_id = str(user.id)
                
                # Delete related bank statements (and their files)
                statements = BankStatement.objects.filter(user_id=username)
                statements_count = statements.count()
                for statement in statements:
                    statement.delete()  # This will also delete the file
                
                # Delete related transactions
                transactions_count = Transaction.objects.filter(owner_id=user_id).delete()[0]
                
                # Delete related accounts
                accounts_count = Account.objects.filter(owner=username).delete()[0]
                
                # Finally, delete the user
                user.delete()
                
                return {
                    "success": True,
                    "message": f"User deleted successfully. Also deleted {accounts_count} account(s), {transactions_count} transaction(s), and {statements_count} bank statement(s).",
                    "deleted_user": user_data,
                    "deleted_counts": {
                        "accounts": accounts_count,
                        "transactions": transactions_count,
                        "bank_statements": statements_count
                    }
                }
            else:
                return {
                    "error": "Invalid password",
                    "message": "Password verification failed"
                }
                
        except User.DoesNotExist:
            return {
                "error": "User not found",
                "message": "No user found with the provided username"
            }
        except Exception as e:
            return {
                "error": "Deletion error",
                "message": f"An error occurred while deleting the user: {str(e)}"
            }
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """
        Retrieves a user by ID.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Optional[User]: User object or None if not found
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """
        Retrieves a user by username.
        
        Args:
            username (str): Username
            
        Returns:
            Optional[User]: User object or None if not found
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
