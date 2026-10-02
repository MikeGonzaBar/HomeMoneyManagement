import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from MoneyManagement.pagination import RelativePageNumberPagination

from .models import BankStatement
from .reconciliation import (
    batch_payload,
    candidate_payload,
    commit_batch,
    create_candidate,
    update_deferred_purchases,
    update_candidate,
    update_import_product,
)
from .serializers import (
    BankStatementResponseSerializer,
    BankStatementUploadSerializer,
    with_review_data,
)
from .services import is_pdf_password_protected, decrypt_pdf_file

logger = logging.getLogger(__name__)


@extend_schema(
    request=BankStatementUploadSerializer,
    responses={
        202: OpenApiResponse(description="Bank statement uploaded and queued"),
        400: OpenApiResponse(description="Invalid upload or password required"),
        502: OpenApiResponse(description="AI processing failed"),
        503: OpenApiResponse(description="AI API key missing"),
    },
)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_bank_statement(request: Request) -> Response:
    """
    Upload a bank statement PDF file.
    
    Expected form data:
    - pdf_file: The PDF file
    - user_id: Ignored if present; ownership comes from the authenticated token
    - pdf_password: (Optional) Password for password-protected PDFs
    
    Returns:
    - 200: Success with file details
    - 400: Bad request (invalid file or missing data, or password required/incorrect)
    - 500: Server error
    """
    
    try:
        # Validate request data
        if 'pdf_file' not in request.FILES:
            return Response({
                'error': 'No PDF file provided',
                'message': 'Please provide a PDF file in the request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the file and derive ownership from the authenticated token.
        pdf_file = request.FILES['pdf_file']
        user_id = request.user.username
        pdf_password = request.data.get('pdf_password', None)  # Optional password
        
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
        
        # Check if PDF is password-protected and handle decryption
        try:
            if is_pdf_password_protected(pdf_file):
                if not pdf_password:
                    return Response({
                        'error': 'Password required',
                        'message': 'This PDF is password-protected. Please provide the password.',
                        'requires_password': True
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Decrypt the PDF
                try:
                    decrypted_pdf = decrypt_pdf_file(pdf_file, pdf_password)
                    # Replace the original file with decrypted version
                    pdf_file = decrypted_pdf
                    logger.info(f"Successfully decrypted password-protected PDF for user {user_id}")
                except ValueError as e:
                    # Password error
                    error_msg = str(e)
                    if "Incorrect password" in error_msg or "decryption failed" in error_msg:
                        return Response({
                            'error': 'Incorrect password',
                            'message': 'The provided password is incorrect. Please try again.',
                            'requires_password': True
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            'error': 'PDF decryption failed',
                            'message': f'Failed to decrypt PDF: {error_msg}'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    logger.error(f"Error decrypting PDF: {str(e)}", exc_info=True)
                    return Response({
                        'error': 'PDF decryption error',
                        'message': f'An error occurred while decrypting the PDF: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # If checking for password protection fails, log but continue
            logger.warning(f"Error checking PDF encryption status: {str(e)}")
        
        # Create the bank statement record
        # Get original filename before potential decryption
        original_filename = request.FILES['pdf_file'].name
        
        # Calculate file size
        if hasattr(pdf_file, 'size'):
            file_size = pdf_file.size
        else:
            # For ContentFile, we need to read to get size
            pdf_file.seek(0, 2)  # Seek to end
            file_size = pdf_file.tell()
            pdf_file.seek(0)  # Reset to beginning
        
        bank_statement = BankStatement.objects.create(
            user_id=user_id,
            owner_user=request.user,
            file=pdf_file,
            original_filename=original_filename,
            file_size=file_size,
            processing_status='pending'
        )
        
        response_data = {
            'message': 'Bank statement uploaded and queued for processing',
            'file_details': {
                'id': bank_statement.id,
                'filename': bank_statement.original_filename,
                'file_size': bank_statement.file_size,
                'file_size_display': bank_statement.get_file_size_display(),
                'upload_date': bank_statement.upload_date.isoformat(),
                'processing_status': bank_statement.processing_status
            },
            'status': 'processing'
        }
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        return Response({
            'error': 'Upload failed',
            'message': f'An error occurred while uploading the file: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(responses={200: OpenApiResponse(description="User bank statements")})
@api_view(['GET'])
def get_user_bank_statements(request: Request, user_id: str) -> Response:
    """
    Get all bank statements for a specific user.
    
    Returns:
    - 200: List of bank statements
    - 404: User not found or no statements
    """
    
    try:
        if user_id != request.user.username:
            return Response({
                'error': 'Cannot access another user\'s bank statements'
            }, status=status.HTTP_403_FORBIDDEN)

        query = with_review_data(
            BankStatement.objects.filter(owner_user=request.user).order_by('-upload_date')
        )
        paginator = RelativePageNumberPagination()
        page = paginator.paginate_queryset(query, request, view=None)
        serializer = BankStatementResponseSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)
        response.data['message'] = f'Found {paginator.page.paginator.count} bank statement(s)'
        response.data['statements'] = serializer.data
        return response
        
    except Exception as e:
        return Response({
            'error': 'Failed to retrieve bank statements',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(responses={200: OpenApiResponse(description="Bank statement details")})
@api_view(['GET'])
def get_bank_statement_details(request: Request, statement_id: int) -> Response:
    """
    Get details of a specific bank statement.
    
    Returns:
    - 200: Bank statement details
    - 404: Statement not found
    """
    
    try:
        bank_statement = with_review_data(
            BankStatement.objects.filter(id=statement_id, owner_user=request.user)
        ).get()
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


@extend_schema(responses={202: OpenApiResponse(description="Bank statement queued for retry")})
@api_view(['POST'])
def retry_bank_statement(request: Request, statement_id: int) -> Response:
    """Queue a failed statement for another background-processing attempt."""
    try:
        bank_statement = BankStatement.objects.get(id=statement_id, owner_user=request.user)
        if bank_statement.processing_status != 'failed':
            return Response({
                'error': 'Statement cannot be retried',
                'message': 'Only failed bank statements can be retried.'
            }, status=status.HTTP_409_CONFLICT)
        bank_statement.processing_status = 'pending'
        bank_statement.processed = False
        bank_statement.error_message = None
        bank_statement.save(update_fields=['processing_status', 'processed', 'error_message'])
        return Response({
            'message': 'Bank statement queued for retry',
            'statement': BankStatementResponseSerializer(bank_statement).data,
        }, status=status.HTTP_202_ACCEPTED)
    except BankStatement.DoesNotExist:
        return Response({
            'error': 'Bank statement not found',
            'message': f'No bank statement found with ID {statement_id}'
        }, status=status.HTTP_404_NOT_FOUND)


@extend_schema(responses={200: OpenApiResponse(description="Bank statement deleted")})
@api_view(['DELETE'])
def delete_bank_statement(request: Request, statement_id: int) -> Response:
    """
    Delete a bank statement.
    
    Returns:
    - 200: Successfully deleted
    - 404: Statement not found
    """
    
    try:
        bank_statement = BankStatement.objects.get(id=statement_id, owner_user=request.user)
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


@extend_schema(responses={200: OpenApiResponse(description="Import batch details")})
@api_view(['GET'])
def get_import_batch(request: Request, batch_id: int) -> Response:
    """Return one import review batch owned by the authenticated user."""
    try:
        batch = request.user.bank_statement_import_batches.get(id=batch_id)
        return Response(batch_payload(batch), status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Import batch not found',
            'message': str(e)
        }, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    request=inline_serializer(
        name="ImportCandidateUpdateRequest",
        fields={
            "title": serializers.CharField(required=False),
            "transaction_type": serializers.CharField(required=False),
            "category": serializers.CharField(required=False),
            "date": serializers.DateField(required=False),
            "amount": serializers.DecimalField(max_digits=14, decimal_places=2, required=False),
            "account_id": serializers.CharField(required=False, allow_blank=True),
            "from_account_id": serializers.CharField(required=False, allow_blank=True),
            "to_account_id": serializers.CharField(required=False, allow_blank=True),
            "source_product_id": serializers.CharField(required=False, allow_blank=True),
            "destination_product_id": serializers.CharField(required=False, allow_blank=True),
            "status": serializers.CharField(required=False),
            "linked_transaction_id": serializers.IntegerField(required=False),
        },
    ),
    responses={200: OpenApiResponse(description="Import candidate updated")},
)
@api_view(['PATCH'])
def update_import_candidate(request: Request, candidate_id: int) -> Response:
    """Update one import review candidate owned by the authenticated user."""
    try:
        candidate = update_candidate(request.user, candidate_id, request.data)
        return Response({'candidate': candidate_payload(candidate)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Failed to update import candidate',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_import_candidate(request: Request, batch_id: int) -> Response:
    """Add one user-entered transaction to an owned review batch."""
    try:
        candidate = create_candidate(request.user, batch_id, request.data)
        return Response({'candidate': candidate_payload(candidate)}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': 'Failed to add import candidate', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        name="ImportProductUpdateRequest",
        fields={
            "name": serializers.CharField(required=False),
            "bank_name": serializers.CharField(required=False, allow_blank=True),
            "product_type": serializers.CharField(required=False),
            "opening_balance": serializers.DecimalField(max_digits=14, decimal_places=2, required=False),
            "closing_balance": serializers.DecimalField(max_digits=14, decimal_places=2, required=False),
        },
    ),
    responses={200: OpenApiResponse(description="Detected statement account updated")},
)
@api_view(['PATCH'])
def update_import_batch_product(request: Request, product_id: int) -> Response:
    """Update one detected account and return its refreshed review batch."""
    try:
        product = update_import_product(request.user, product_id, request.data)
        return Response({'import_batch': batch_payload(product.import_batch)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Failed to update detected account', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def update_import_batch_msi(request: Request, batch_id: int) -> Response:
    """Save the reviewed MSI schedule for a credit-card import batch."""
    try:
        batch = update_deferred_purchases(request.user, batch_id, request.data.get('deferred_purchases'))
        return Response({'deferred_purchases': batch.deferred_purchases}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Failed to update MSI details', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        name="ImportBatchCommitRequest",
        fields={"account_id": serializers.CharField(required=False, allow_blank=True)},
    ),
    responses={200: OpenApiResponse(description="Import batch committed")},
)
@api_view(['POST'])
def commit_import_batch(request: Request, batch_id: int) -> Response:
    """Commit an import review batch owned by the authenticated user."""
    try:
        result = commit_batch(request.user, batch_id, request.data)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Failed to commit import batch',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
