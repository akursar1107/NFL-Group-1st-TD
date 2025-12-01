"""
Standardized error handling for API endpoints
"""
from flask import jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message, status_code=500, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def handle_api_errors(f):
    """
    Decorator to standardize error handling across API endpoints.
    
    Usage:
        @api_bp.route('/endpoint')
        @handle_api_errors
        def my_endpoint():
            # Your code here
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.error(f"API Error in {f.__name__}: {e.message}", exc_info=True)
            response = {
                'success': False,
                'error': e.message
            }
            if e.details:
                response['details'] = e.details
            return jsonify(response), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred',
                'message': str(e)
            }), 500
    
    return wrapper


def success_response(data, status_code=200):
    """
    Create a standardized success response.
    
    Args:
        data: The data to return (dict)
        status_code: HTTP status code (default 200)
    
    Returns:
        Flask JSON response with success=True
    """
    response = {'success': True}
    response.update(data)
    return jsonify(response), status_code


def error_response(message, status_code=400, details=None):
    """
    Create a standardized error response.
    
    Args:
        message: Error message string
        status_code: HTTP status code (default 400)
        details: Optional additional error details
    
    Returns:
        Flask JSON response with success=False
    """
    response = {
        'success': False,
        'error': message
    }
    if details:
        response['details'] = details
    return jsonify(response), status_code
