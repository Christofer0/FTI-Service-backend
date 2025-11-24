
# utils/jwt_utils.py
import functools
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity as get_jwt_id
from app.models.user_model import User
from app.models.dosen_model import Dosen

def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_id()
    if not user_id:
        return None
    usr = User.query.get(user_id)
    if usr.role == "dosen":
        ttd_path = Dosen.query.get(user_id).ttd_path
        usr.ttd_path = ttd_path
    return usr

def role_required(*allowed_roles):
    """Decorator to check user role"""
    def decorator(f):
        @functools.wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            if not current_user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Account is deactivated'
                }), 403
            
            if current_user.role not in allowed_roles:
                return jsonify({
                    'success': False,
                    'message': 'Insufficient permissions'
                }), 403
            
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator

def get_jwt_identity():
    """Get JWT identity (user_id)"""
    return get_jwt_id()
