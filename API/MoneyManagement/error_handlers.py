"""
Custom error handling for the Money Management API.
Provides consistent error responses across all endpoints.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    
    Args:
        exc: The exception that was raised
        context: The context in which the exception occurred
        
    Returns:
        Response: Standardized error response
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Get the error details
        error_details = response.data
        
        # Create standardized error response
        custom_response_data = {
            "success": False,
            "error": {
                "type": get_error_type(exc),
                "message": get_error_message(exc, error_details),
                "details": error_details if isinstance(error_details, dict) else {"errors": error_details},
                "status_code": response.status_code
            }
        }
        
        response.data = custom_response_data
        
        # Log the error
        logger.error(f"API Error: {exc.__class__.__name__} - {custom_response_data['error']['message']}")
    
    return response


def get_error_type(exc):
    """Get a user-friendly error type."""
    error_type_mapping = {
        ValidationError: "validation_error",
        IntegrityError: "database_error",
        PermissionError: "permission_error",
        ValueError: "value_error",
        TypeError: "type_error",
        KeyError: "key_error",
        AttributeError: "attribute_error"
    }
    
    return error_type_mapping.get(type(exc), "unknown_error")


def get_error_message(exc, error_details):
    """Get a user-friendly error message."""
    if isinstance(exc, ValidationError):
        return "Validation failed. Please check your input data."
    elif isinstance(exc, IntegrityError):
        return "Database constraint violation. The operation could not be completed."
    elif isinstance(exc, PermissionError):
        return "You don't have permission to perform this action."
    elif isinstance(error_details, dict) and 'detail' in error_details:
        return str(error_details['detail'])
    elif isinstance(error_details, list) and len(error_details) > 0:
        return str(error_details[0])
    else:
        return "An unexpected error occurred. Please try again later."


def create_error_response(message, error_type="error", status_code=400, details=None):
    """
    Create a standardized error response.
    
    Args:
        message (str): Error message
        error_type (str): Type of error
        status_code (int): HTTP status code
        details (dict): Additional error details
        
    Returns:
        Response: Standardized error response
    """
    return Response(
        {
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
                "details": details or {},
                "status_code": status_code
            }
        },
        status=status_code
    )


def create_success_response(data=None, message="Success", status_code=200):
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message (str): Success message
        status_code (int): HTTP status code
        
    Returns:
        Response: Standardized success response
    """
    response_data = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response_data["data"] = data
    
    return Response(response_data, status=status_code)
