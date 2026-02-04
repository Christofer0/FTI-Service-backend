from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.auth_manual_service import AuthManualService
from schemas.auth_manual_schema import (
    CheckEmailSchema,
    CompleteProfileMahasiswaManualSchema,
    CompleteProfileAdminManualSchema,
    CompleteProfileDosenManualSchema,
    LoginManualSchema
)
from schemas.user_schema import UserSchema
from utils.response_utils import success_response, error_response

auth_manual_bp = Blueprint('auth_manual', __name__)
auth_manual_service = AuthManualService()

# Schema instances
check_email_schema = CheckEmailSchema()
complete_profile_mahasiswa_schema = CompleteProfileMahasiswaManualSchema()
complete_profile_admin_schema = CompleteProfileAdminManualSchema()
complete_profile_dosen_schema = CompleteProfileDosenManualSchema()
login_schema = LoginManualSchema()
user_schema = UserSchema()


@auth_manual_bp.route('/register/check-email', methods=['POST'])
def check_email():
    """
    Check email eligibility for registration
    Request body: { "email": "712021001@student.uksw.edu" }
    
    Response:
    - 200: Email eligible, returns role and necessary data
    - 400: Email not eligible or already registered
    """
    try:
        # Validate request
        data = check_email_schema.load(request.json)
        email = data['email']
        
        # Check eligibility
        result, error = auth_manual_service.check_email_eligibility(email)
        
        if error:
            return error_response(error, status_code=400)
        
        role = result.get('role')
        
        if role == 'mahasiswa':
            return success_response(
                "Silakan lengkapi profil Anda",
                {
                    'needs_profile': True,
                    'role': role,
                    'nomor_induk': result.get('nomor_induk'),
                    'prodi_id': result.get('prodi_id'),
                    'fakultas_id': result.get('fakultas_id'),
                    'email': email
                },
                status_code=200
            )
        
        elif role == 'admin':
            return success_response(
                "Silakan lengkapi profil Admin",
                {
                    'needs_profile': True,
                    'role': role,
                    'email': email
                },
                status_code=200
            )
        
        elif role == 'dosen':
            return success_response(
                "Silakan lengkapi profil Dosen",
                {
                    'needs_profile': True,
                    'role': role,
                    'email': email,
                    'nomor_induk': result.get('nomor_induk')  # if pre-filled from dosen_allowed
                },
                status_code=200
            )
        
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)
    except Exception as e:
        return error_response("Gagal memeriksa email", str(e), 500)


@auth_manual_bp.route('/register/complete-profile/mahasiswa', methods=['POST'])
def complete_profile_mahasiswa():
    """
    Complete mahasiswa profile after email check
    Request body: {
        "email": "712021001@student.uksw.edu",
        "nama": "John Doe",
        "password": "password123",
        "semester": 5,
        "no_hp": "081234567890"
    }
    """
    try:
        # Validate request
        data = complete_profile_mahasiswa_schema.load(request.json)
        
        # Create mahasiswa user
        result, error = auth_manual_service.create_mahasiswa_manual(
            email=data['email'],
            nama=data['nama'],
            password=data['password'],
            semester=data['semester'],
            no_hp=data['no_hp']
        )
        
        if error:
            return error_response(error, status_code=400)
        
        # Get mahasiswa data
        from app.models.mahasiswa_model import Mahasiswa
        from schemas.mahasiswa_schema import MahasiswaSchema
        
        mahasiswa = Mahasiswa.query.filter_by(user_id=result['user'].id).first()
        mahasiswa_data = MahasiswaSchema().dump(mahasiswa) if mahasiswa else None
        
        response_data = {
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'expires_in': 3600,
            'user': user_schema.dump(result['user']),
            'mahasiswa': mahasiswa_data
        }
        
        return success_response("Registrasi berhasil! Selamat datang", response_data, 201)
        
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)
    except Exception as e:
        return error_response("Registrasi gagal", str(e), 500)


@auth_manual_bp.route('/register/complete-profile/admin', methods=['POST'])
def complete_profile_admin():
    """
    Complete admin profile after email check
    Request body: {
        "email": "admin@uksw.edu",
        "nama": "Admin UKSW",
        "password": "password123",
        "nomor_induk": "A001",
        "no_hp": "081234567890"
    }
    """
    try:
        # Validate request
        data = complete_profile_admin_schema.load(request.json)
        
        # Create admin user
        result, error = auth_manual_service.create_admin_manual(
            email=data['email'],
            nama=data['nama'],
            password=data['password'],
            nomor_induk=data['nomor_induk'],
            no_hp=data['no_hp']
        )
        
        if error:
            return error_response(error, status_code=400)
        
        response_data = {
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'expires_in': 3600,
            'user': user_schema.dump(result['user'])
        }
        
        return success_response("Registrasi berhasil! Selamat datang Admin", response_data, 201)
        
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)
    except Exception as e:
        return error_response("Registrasi gagal", str(e), 500)


@auth_manual_bp.route('/register/complete-profile/dosen', methods=['POST'])
def complete_profile_dosen():
    """
    Complete dosen profile after email check
    Accepts multipart/form-data for signature file upload
    """
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        # Validate form data
        data = complete_profile_dosen_schema.load(form_data)
        
        # Handle signature file
        signature_file = None
        if 'tanda_tangan' in request.files or 'signature' in request.files:
            signature_file = request.files.get('tanda_tangan') or request.files.get('signature')
            
            if signature_file and signature_file.filename != '':
                from utils.file_utils import is_signature_file
                if not is_signature_file(signature_file.filename):
                    return error_response(
                        "File tanda tangan harus berformat PNG, JPG, JPEG, atau GIF",
                        status_code=400
                    )
            else:
                signature_file = None
        
        # Create dosen user
        result, error = auth_manual_service.create_dosen_manual(
            email=data['email'],
            nama=data['nama'],
            password=data['password'],
            nomor_induk=data['nomor_induk'],
            no_hp=data['no_hp'],
            gelar_depan=data.get('gelar_depan'),
            gelar_belakang=data.get('gelar_belakang'),
            jabatan=data.get('jabatan'),
            fakultas_id=data['fakultas_id'],
            signature_file=signature_file
        )
        
        if error:
            return error_response(error, status_code=400)
        
        # Get dosen data
        from app.models.dosen_model import Dosen
        from schemas.dosen_schema import DosenSchema
        
        dosen = Dosen.query.filter_by(user_id=result['user'].id).first()
        dosen_data = DosenSchema().dump(dosen) if dosen else None
        
        response_data = {
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'expires_in': 3600,
            'user': user_schema.dump(result['user']),
            'dosen': dosen_data
        }
        
        return success_response("Registrasi berhasil! Selamat datang", response_data, 201)
        
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)
    except Exception as e:
        return error_response("Registrasi gagal", str(e), 500)


@auth_manual_bp.route('/login', methods=['POST'])
def login():
    """
    Manual login endpoint
    Request body: {
        "nomor_induk": "712021001",
        "password": "password123"
    }
    """
    try:
        # Validate request
        data = login_schema.load(request.json)
        
        # Authenticate user
        result, error = auth_manual_service.login_manual(
            nomor_induk=data['nomor_induk'],
            password=data['password']
        )
        
        if error:
            return error_response(error, status_code=401)
        
        user = result['user']
        
        # Get additional data based on role
        additional_data = None
        
        if user.role == 'mahasiswa':
            from app.models.mahasiswa_model import Mahasiswa
            from schemas.mahasiswa_schema import MahasiswaSchema
            
            mahasiswa = Mahasiswa.query.filter_by(user_id=user.id).first()
            if mahasiswa:
                additional_data = MahasiswaSchema().dump(mahasiswa)
        
        elif user.role == 'dosen':
            from app.models.dosen_model import Dosen
            from schemas.dosen_schema import DosenSchema
            
            dosen = Dosen.query.filter_by(user_id=user.id).first()
            if dosen:
                additional_data = DosenSchema().dump(dosen)
        
        # Build response (same format as Google login)
        response_data = {
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'expires_in': 3600,
            'user': user_schema.dump(user),
            f'{user.role}': additional_data  # 'mahasiswa' or 'dosen' or None for admin
        }
        
        return success_response("Login berhasil", response_data)
        
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)
    except Exception as e:
        return error_response("Login gagal", str(e), 500)


@auth_manual_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        from flask_jwt_extended import create_access_token
        
        user_id = get_jwt_identity()
        access_token = create_access_token(identity=user_id)
        
        return success_response(
            "Token refreshed",
            {
                'access_token': access_token,
                'expires_in': 3600
            }
        )
        
    except Exception as e:
        return error_response("Token refresh failed", str(e), 500)