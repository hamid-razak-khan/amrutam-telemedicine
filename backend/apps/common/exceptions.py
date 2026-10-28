from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import OperationalError, IntegrityError
import logging

logger = logging.getLogger('amrutam')

def custom_exception_handler(exc, context):
    """
    Standardized REST API error response handler.
    Always produces a consistent format:
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable summary",
            "details": {...}
        }
    }
    """
    # Check for database concurrency lock or integrity collision
    if isinstance(exc, OperationalError) and ('locked' in str(exc).lower() or 'busy' in str(exc).lower()):
        return Response(
            {
                'success': False,
                'error': {
                    'code': 'CONCURRENCY_CONFLICT',
                    'message': 'This resource is currently locked by a competing concurrent transaction. Please retry.',
                    'details': {'operational_error': str(exc)}
                }
            },
            status=status.HTTP_409_CONFLICT
        )

    if isinstance(exc, IntegrityError):
        err_str = str(exc).lower()
        if 'slot' in err_str or 'unique_active' in err_str or 'consultation' in err_str:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'SLOT_UNAVAILABLE',
                        'message': 'Sorry, this time slot has just been booked. Please select another available time.',
                        'details': {'integrity_error': 'Slot conflict detected at database level.'}
                    }
                },
                status=status.HTTP_409_CONFLICT
            )

    response = exception_handler(exc, context)

    if response is not None:
        error_code = 'API_ERROR'
        message = 'An error occurred while processing your request.'

        # Check if exception or detail defines a specific error code
        custom_code = None
        if hasattr(exc, 'default_code') and exc.default_code not in ('error', 'permission_denied', 'not_authenticated', 'invalid'):
            custom_code = exc.default_code
        elif hasattr(exc, 'code') and exc.code not in ('error', 'permission_denied', 'not_authenticated', 'invalid'):
            custom_code = exc.code
        elif isinstance(response.data, dict) and 'detail' in response.data and hasattr(response.data['detail'], 'code'):
            detail_code = response.data['detail'].code
            if detail_code and detail_code not in ('error', 'permission_denied', 'not_authenticated', 'invalid'):
                custom_code = str(detail_code).upper()

        if custom_code:
            error_code = custom_code
        elif response.status_code == 400:
            error_code = 'VALIDATION_ERROR'
            message = 'Invalid request payload or parameters.'
        elif response.status_code == 401:
            error_code = 'AUTHENTICATION_REQUIRED'
            message = 'Authentication credentials were not provided or are invalid.'
        elif response.status_code == 403:
            error_code = 'PERMISSION_DENIED'
            message = 'You do not have permission to perform this action.'
        elif response.status_code == 404:
            error_code = 'NOT_FOUND'
            message = 'The requested resource was not found.'
        elif response.status_code == 409:
            error_code = 'CONFLICT'
            message = 'Conflict with the current state of the resource.'
        elif response.status_code == 429:
            error_code = 'THROTTLED'
            message = 'Request rate limit exceeded. Please try again later.'

        # If data is a dict and has detail
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                message = str(response.data['detail'])
            details = response.data
        elif isinstance(response.data, list):
            details = {'non_field_errors': response.data}
        else:
            details = {'error': str(response.data)}

        response.data = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
                'details': details
            }
        }
    else:
        logger.exception("Unhandled server exception: %s", exc)
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'An unexpected error occurred on the server.',
                    'details': {}
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
