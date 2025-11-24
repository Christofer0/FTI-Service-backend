# controllers/auth_controller.py
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.auth_service import AuthService
from schemas.auth_schema import LoginSchema, RegisterSchema, TokenResponseSchema
from schemas.user_schema import UserSchema
from utils.response_utils import success_response, error_response

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

# Schema instances
login_schema = LoginSchema()
register_schema = RegisterSchema()
token_response_schema = TokenResponseSchema()
user_schema = UserSchema()

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        # Validate request data
        login_data = login_schema.load(request.json)
        
        # Authenticate user
        result, error = auth_service.login(
            login_data['nomor_induk'],
            login_data['password']
        )
        
        if error:
            return error_response(error, status_code=401)
        
        user = result['user']
        
        # Ambil data dosen kalau role = dosen
        dosen_data = None
        if user.role == "dosen":
            from app.models.dosen_model import Dosen
            from schemas.dosen_schema import DosenSchema

            dosen = Dosen.query.filter_by(user_id=user.id).first()
            if dosen:
                dosen_data = DosenSchema().dump(dosen)

        # Serialize response
        response_data = {
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'expires_in': 3600,  # 1 hour
            'user': user_schema.dump(user),
            'dosen': dosen_data   # ✅ tambahin ini kalau role dosen
        }
        
        return success_response("Login successful", response_data)
        
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)
    except Exception as e:
        return error_response("Login failed", str(e), 500)

@auth_bp.route('/login/google', methods=['POST'])
def login_with_google():
    """User login with Google OAuth"""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return error_response("Google token is required", status_code=400)
        
        google_token = data['token']
        
        # Authenticate with Google
        result, error = auth_service.login_with_google(google_token)
        
        if error:
            return error_response(error, status_code=401)
        
        if result.get('action') == 'complete_profile':
            return success_response(
                "Lengkapi profil terlebih dahulu",
                result,
                status_code=200
            )
        
        user = result['user']
        
        # Ambil data dosen kalau role = dosen
        dosen_data = None
        if user.role == "dosen":
            from app.models.dosen_model import Dosen
            from schemas.dosen_schema import DosenSchema

            dosen = Dosen.query.filter_by(user_id=user.id).first()
            if dosen:
                dosen_data = DosenSchema().dump(dosen)

        # Serialize response
        response_data = {
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'expires_in': 3600,  # 1 hour
            'user': user_schema.dump(user),
            'dosen': dosen_data
        }
        
        return success_response("Google login successful", response_data)
        
    except Exception as e:
        return error_response("Google login failed", str(e), 500)


@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        # Validate request data
        register_data = register_schema.load(request.json)
        
        # Register user
        user, error = auth_service.register(register_data)
        
        if error:
            return error_response(error, status_code=400)
        
        # Serialize response
        user_data = user_schema.dump(user)
        return success_response("Registration successful", user_data, 201)
        
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)
    except Exception as e:
        return error_response("Registration failed", str(e), 500)

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        user_id = get_jwt_identity()
        result, error = auth_service.refresh_token(user_id)
        
        if error:
            return error_response(error, status_code=401)
        
        return success_response("Token refreshed", result)
        
    except Exception as e:
        return error_response("Token refresh failed", str(e), 500)

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    try:
        from utils.jwt_utils import get_current_user
        user = get_current_user()
        
        if not user:
            return error_response("User not found", status_code=404)
        
        user_data = user_schema.dump(user)
        return success_response("User retrieved", user_data)
        
    except Exception as e:
        return error_response("Failed to get user", str(e), 500)