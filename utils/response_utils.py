
# utils/response_utils.py
from flask import jsonify

def success_response(message="Success", data=None, status_code=200):
    """Create success response"""
    response = {
        'success': True,
        'message': message
    }
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code

def error_response(message="Error occurred", errors=None, status_code=400):
    """Create error response"""
    response = {
        'success': False,
        'message': message
    }
    if errors:
        response['errors'] = errors
    
    return jsonify(response), status_code

def paginated_response(data, pagination, message="Success", status_code=200):
    """Create paginated response"""
    response = {
        'success': True,
        'message': message,
        'data': data,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }
    
    return jsonify(response), status_code
