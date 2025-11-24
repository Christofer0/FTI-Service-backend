# utils/error_handlers.py
from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended.exceptions import JWTExtendedException

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.messages
        }), 400
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        return jsonify({
            'success': False,
            'message': 'Database integrity error. Data might already exist.'
        }), 409
    
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_exceptions(e):
        return jsonify({
            'success': False,
            'message': str(e)
        }), 401
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({
            'success': False,
            'message': e.description
        }), e.code
    
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            'success': False,
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

