from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password

from .models import User
from .serializers import UserSerializer, UserLoginSerializer, UserResponseSerializer
from .services import UserService
from MoneyManagement.error_handlers import create_success_response, create_error_response


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration with backward compatibility.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Create a new user account."""
        # Check if this is a legacy registration (missing email and password_confirm)
        is_legacy = not request.data.get('email') and not request.data.get('password_confirm')
        
        if is_legacy:
            # Legacy format: create user with minimal data
            try:
                # Use service for legacy registration
                result = UserService.create_user({
                    'username': request.data.get('username'),
                    'password': request.data.get('password'),
                    'first_name': request.data.get('first_name'),
                    'last_name': request.data.get('last_name')
                })
                
                if result.get('success'):
                    # Return legacy format
                    return Response(result['user'], status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        "error": result.get('message', 'Registration failed')
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    "error": "Registration failed"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # New format: use serializer validation
            serializer = self.get_serializer(data=request.data)
            
            if serializer.is_valid():
                try:
                    user = serializer.save()
                    response_serializer = UserResponseSerializer(user)
                    return create_success_response(
                        data=response_serializer.data,
                        message="User registered successfully",
                        status_code=status.HTTP_201_CREATED
                    )
                except Exception as e:
                    return create_error_response(
                        message="Failed to create user account",
                        error_type="registration_error",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return create_error_response(
                    message="Invalid registration data",
                    error_type="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    details=serializer.errors
                )


class UserLoginView(generics.GenericAPIView):
    """
    API endpoint for user login with backward compatibility.
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Authenticate user and return user data."""
        # Handle backward compatibility - check if username is in URL
        username_from_url = kwargs.get('username')
        
        if username_from_url:
            # Legacy format: POST /user/{username}/ with {password: "..."}
            password = request.data.get('password')
            if not password:
                return create_error_response(
                    message="Password is required",
                    error_type="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            username_or_email = username_from_url
        else:
            # New format: POST /user/login/ with {username_or_email: "...", password: "..."}
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return create_error_response(
                    message="Invalid login data",
                    error_type="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    details=serializer.errors
                )
            username_or_email = serializer.validated_data['username_or_email']
            password = serializer.validated_data['password']
        
        # Use service for authentication
        result = UserService.authenticate_user(username_or_email, password)
        
        if result.get('success'):
            # For backward compatibility, return the old format if it's a legacy request
            if username_from_url:
                return Response({
                    "user": result['user'],
                    "valid": True
                }, status=status.HTTP_200_OK)
            else:
                return create_success_response(
                    data=result['user'],
                    message=result['message'],
                    status_code=status.HTTP_200_OK
                )
        else:
            # For backward compatibility, return the old format if it's a legacy request
            if username_from_url:
                return Response({
                    "valid": False,
                    "error": result['message']
                }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return create_error_response(
                    message=result['message'],
                    error_type="authentication_error",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for user detail operations (get, update, delete).
    """
    queryset = User.objects.all()
    serializer_class = UserResponseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'username'

    def get(self, request, *args, **kwargs):
        """Get user details."""
        try:
            user = self.get_object()
            serializer = self.get_serializer(user)
            return create_success_response(
                data=serializer.data,
                message="User details retrieved successfully"
            )
        except User.DoesNotExist:
            return create_error_response(
                message="User not found",
                error_type="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, *args, **kwargs):
        """Delete user account."""
        try:
            user = self.get_object()
            password = request.data.get('password')
            
            if not password:
                return create_error_response(
                    message="Password required for account deletion",
                    error_type="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Use service for deletion
            result = UserService.delete_user(user.username, password)
            
            if result.get('success'):
                return create_success_response(
                    data=result['deleted_user'],
                    message=result['message'],
                    status_code=status.HTTP_200_OK
                )
            else:
                return create_error_response(
                    message=result['message'],
                    error_type="deletion_error",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except User.DoesNotExist:
            return create_error_response(
                message="User not found",
                error_type="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user's profile.
    """
    serializer = UserResponseSerializer(request.user)
    return create_success_response(
        data=serializer.data,
        message="Profile retrieved successfully"
    )


@api_view(['PUT'])
@permission_classes([AllowAny])  # We'll validate the user manually
def update_user_info(request):
    """
    Update user information (username, first_name, last_name).
    """
    try:
        username = request.data.get('username')
        if not username:
            return Response({
                'error': 'Username is required',
                'message': 'Please provide a username'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found',
                'message': f'No user found with username: {username}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update user information
        new_username = request.data.get('new_username', user.username)
        first_name = request.data.get('first_name', user.first_name)
        last_name = request.data.get('last_name', user.last_name)
        
        # Check if new username is already taken (if it's different)
        if new_username != user.username:
            if User.objects.filter(username=new_username).exists():
                return Response({
                    'error': 'Username already exists',
                    'message': f'Username "{new_username}" is already taken'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the user
        user.username = new_username
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        return Response({
            'message': 'User information updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Update failed',
            'message': f'An error occurred while updating user information: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([AllowAny])  # We'll validate the user manually
def change_password(request):
    """
    Change user password with current password verification.
    """
    try:
        username = request.data.get('username')
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not all([username, current_password, new_password]):
            return Response({
                'error': 'Missing required fields',
                'message': 'Please provide username, current_password, and new_password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found',
                'message': f'No user found with username: {username}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify current password
        if not user.check_password(current_password):
            return Response({
                'error': 'Invalid current password',
                'message': 'The current password you entered is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password
        if len(new_password) < 8:
            return Response({
                'error': 'Password too short',
                'message': 'New password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Password change failed',
            'message': f'An error occurred while changing password: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
