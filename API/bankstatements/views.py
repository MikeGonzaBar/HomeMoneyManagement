from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.files.storage import default_storage
import os
import mimetypes

from .models import BankStatement
from .serializers import BankStatementUploadSerializer, BankStatementResponseSerializer


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_bank_statement(request):
    """
    Upload a bank statement PDF file.
    
    Expected form data:
    - pdf_file: The PDF file
    - user_id: The username of the user uploading the file
    
    Returns:
    - 200: Success with file details
    - 400: Bad request (invalid file or missing data)
    - 500: Server error
    """
    
    try:
        # Validate request data
        if 'pdf_file' not in request.FILES:
            return Response({
                'error': 'No PDF file provided',
                'message': 'Please provide a PDF file in the request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'user_id' not in request.data:
            return Response({
                'error': 'No user_id provided',
                'message': 'Please provide a user_id in the request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the file and user_id
        pdf_file = request.FILES['pdf_file']
        user_id = request.data['user_id']
        
        # Validate file type
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response({
                'error': 'Invalid file type',
                'message': 'Only PDF files are allowed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (10MB limit)
        if pdf_file.size > 10 * 1024 * 1024:
            return Response({
                'error': 'File too large',
                'message': 'File size must be less than 10MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate PDF content by checking the header
        pdf_file.seek(0)
        header = pdf_file.read(4)
        pdf_file.seek(0)  # Reset file pointer
        
        if not header.startswith(b'%PDF'):
            return Response({
                'error': 'Invalid PDF file',
                'message': 'File does not appear to be a valid PDF'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the bank statement record
        bank_statement = BankStatement.objects.create(
            user_id=user_id,
            file=pdf_file,
            original_filename=pdf_file.name,
            file_size=pdf_file.size,
            processing_status='pending'
        )
        
        # Prepare response data
        response_data = {
            'message': 'Bank statement uploaded successfully',
            'file_details': {
                'id': bank_statement.id,
                'filename': bank_statement.original_filename,
                'file_size': bank_statement.file_size,
                'file_size_display': bank_statement.get_file_size_display(),
                'upload_date': bank_statement.upload_date.isoformat(),
                'processing_status': bank_statement.processing_status
            },
            'status': 'success'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Upload failed',
            'message': f'An error occurred while uploading the file: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_user_bank_statements(request, user_id):
    """
    Get all bank statements for a specific user.
    
    Returns:
    - 200: List of bank statements
    - 404: User not found or no statements
    """
    
    try:
        bank_statements = BankStatement.objects.filter(user_id=user_id).order_by('-upload_date')
        
        if not bank_statements.exists():
            return Response({
                'message': 'No bank statements found for this user',
                'statements': []
            }, status=status.HTTP_200_OK)
        
        serializer = BankStatementResponseSerializer(bank_statements, many=True)
        
        return Response({
            'message': f'Found {bank_statements.count()} bank statement(s)',
            'statements': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to retrieve bank statements',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_bank_statement_details(request, statement_id):
    """
    Get details of a specific bank statement.
    
    Returns:
    - 200: Bank statement details
    - 404: Statement not found
    """
    
    try:
        bank_statement = BankStatement.objects.get(id=statement_id)
        serializer = BankStatementResponseSerializer(bank_statement)
        
        return Response({
            'message': 'Bank statement details retrieved successfully',
            'statement': serializer.data
        }, status=status.HTTP_200_OK)
        
    except BankStatement.DoesNotExist:
        return Response({
            'error': 'Bank statement not found',
            'message': f'No bank statement found with ID {statement_id}'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'error': 'Failed to retrieve bank statement',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_bank_statement(request, statement_id):
    """
    Delete a bank statement.
    
    Returns:
    - 200: Successfully deleted
    - 404: Statement not found
    """
    
    try:
        bank_statement = BankStatement.objects.get(id=statement_id)
        filename = bank_statement.original_filename
        bank_statement.delete()
        
        return Response({
            'message': f'Bank statement "{filename}" deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except BankStatement.DoesNotExist:
        return Response({
            'error': 'Bank statement not found',
            'message': f'No bank statement found with ID {statement_id}'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'error': 'Failed to delete bank statement',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)