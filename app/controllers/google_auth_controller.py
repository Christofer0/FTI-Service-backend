# ============================================
# FILE 2: app/controllers/google_auth_controller.py
# ============================================
from flask import Blueprint, request, jsonify, redirect
from marshmallow import ValidationError, Schema, fields
import os

from app.services.google_oauth_service import GoogleOAuthService
from schemas.user_schema import UserSchema
from utils.response_utils import success_response, error_response
from werkzeug.datastructures import FileStorage


google_auth_bp = Blueprint('google_auth', __name__)
google_oauth_service = GoogleOAuthService()
user_schema = UserSchema()

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')


# Validation Schemas
class GoogleTokenSchema(Schema):
    """Schema for Google token validation"""
    token = fields.Str(required=True)


class CompleteProfileMahasiswaSchema(Schema):
    """Schema for completing mahasiswa profile"""
    token = fields.Str(required=True)  # Google token
    semester = fields.Int(required=True, validate=lambda x: 1 <= x <= 14)
    no_hp = fields.Str(required=True)

class CompleteProfileAdminSchema(Schema):
    """Schema for completing admin profile"""
    token = fields.Str(required=True)
    nomor_induk = fields.Str(required=True)
    no_hp = fields.Str(required=True)


class CompleteProfileDosenSchema(Schema):
    """Schema for completing dosen profile"""
    token = fields.Str(required=True)
    nomor_induk = fields.Str(required=True)
    no_hp = fields.Str(required=True)
    gelar_depan = fields.Str(required=False, allow_none=True)
    gelar_belakang = fields.Str(required=False, allow_none=True)
    jabatan = fields.Str(required=False, allow_none=True)
    fakultas_id = fields.Int(required=True)



google_token_schema = GoogleTokenSchema()
complete_profile_mahasiswa_schema = CompleteProfileMahasiswaSchema()
complete_profile_admin_schema = CompleteProfileAdminSchema()
complete_profile_dosen_schema = CompleteProfileDosenSchema()


@google_auth_bp.route('/google/login', methods=['POST'])
def google_login():
    """
    Google OAuth login endpoint
    Request body: { "token": "google_oauth_token" }
    """
    try:
        # Validate request
        data = google_token_schema.load(request.json)
        google_token = data['token']
        
        # Process Google login
        result, error = google_oauth_service.process_google_login(google_token)
        
        if error:
            return error_response(error, status_code=400)
        
        # Check if user needs to complete profile
        if result.get('needs_profile'):
            role = result.get('role')
            
            if role == 'mahasiswa':
                # Return data needed for profile completion
                return success_response(
                    "Silakan lengkapi profil Anda",
                    {
                        'needs_profile': True,
                        'role': role,
                        'nomor_induk': result.get('nomor_induk'),
                        'prodi_id': result.get('prodi_id'),
                        'email': result['google_data']['email'],
                        'nama': result['google_data']['name'],
                        'picture': result['google_data'].get('picture')
                    },
                    status_code=206  # 206 Partial Content - needs more info
                )
            
            elif role == 'admin': # or role == 'dosen'
                return success_response(
                    "Silakan lengkapi profil Anda",
                    {
                        'needs_profile': True,
                        'role': role,
                        'email':result.get('google_data')['email'],
                        'nama':result.get('google_data')['name'],
                        'picture': result['google_data'].get('picture')
                    },
                    status_code=206
                )
            elif role == 'dosen':
                # For dosen, return message that registration not implemented yet
                return success_response(
                    'SIlahkan lengkapi profil Anda',
                    {
                        'needs_profile': True,
                        'role':role,
                        'email':result.get('google_data')['email'],
                        'nama':result.get('google_data')['name']
                    },
                    status_code=206
                )
        
        # User already exists, return tokens
        # Ambil data tambahan berdasarkan role
        additional_data = None
        user = result['user']
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
        print(str(e),"error")
        return error_response("Login gagal", str(e), 500)


@google_auth_bp.route('/google/complete-profile/mahasiswa', methods=['POST'])
def complete_profile_mahasiswa():
    """
    Complete profile for new mahasiswa after Google login
    Request body: {
        "token": "google_oauth_token",
        "semester": 1,
        "no_hp": "081234567890"
    }
    """
    try:
        # Validate request
        data = complete_profile_mahasiswa_schema.load(request.json)
        
        # Verify Google token and get user data
        google_data, error = google_oauth_service.verify_google_token(data['token'])
        if error:
            return error_response(error, status_code=400)
        
        # Create mahasiswa user
        result, error = google_oauth_service.create_mahasiswa_from_google(
            google_data=google_data,
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


@google_auth_bp.route('/google/complete-profile/admin', methods=['POST'])
def complete_profile_admin():
    """
    Complete profile for new admin after Google login
    Request body: {
        "token": "google_oauth_token",
        "nomor_induk": "A001",
        "no_hp": "081234567890"
    }
    """
    try:
        # Validate request
        data = complete_profile_admin_schema.load(request.json)
        
        # Verify Google token and get user data
        google_data, error = google_oauth_service.verify_google_token(data['token'])
        if error:
            return error_response(error, status_code=400)
        
        # Create admin user
        result, error = google_oauth_service.create_admin_from_google(
            google_data=google_data,
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
    
# @google_auth_bp.route('/google/complete-profile/dosen', methods=['POST'])
# def complete_profile_dosen():
#     """
#     Complete profile for new dosen after Google login
#     Supports multipart/form-data for file upload
    
#     Form fields:
#     - token: google_oauth_token
#     - nomor_induk: NIP/NIDN dosen
#     - no_hp: Nomor HP
#     - gelar_depan: Gelar depan (optional)
#     - gelar_belakang: Gelar belakang (optional)
#     - jabatan: Jabatan (optional)
#     - fakultas_id: ID fakultas
#     - signature: File upload tanda tangan (optional)
#     """
#     try:    
#         form_data = request.form.to_dict()

#         # validate req
#         data = complete_profile_dosen_schema.load(form_data)

#         signature_file = None
#         if 'signature' in request.files:
#             signature_file = request.files.get('signature')
#             if signature_file.filename == '':
#                 signature_file = None
#             else:
#                 # Additional validation for signature file
#                 from utils.file_utils import is_signature_file  # If you add this function
#                 if not is_signature_file(signature_file.filename):
#                     return error_response(
#                         "File tanda tangan harus berformat PNG, JPG, JPEG, atau GIF",
#                         status_code=400
#                     )

#         #Verify Google token and get user data
#         google_data, error = google_oauth_service.verify_google_token(data['token'])
#         if error:
#             return error_response(error, status_code=400)
        
#         result, error = google_oauth_service.create_dosen_from_google(
#             google_data=google_data,
#             nomor_induk=data['nomor_induk'],
#             no_hp=data['no_hp'],
#             gelar_depan=data.get('gelar_depan'),
#             gelar_belakang=data.get('gelar_belakang'),
#             jabatan=data.get('jabatan'),
#             fakultas_id=data['fakultas_id'],
#             signature_file=signature_file
#         )

#         if error:
#             return error_response(error, status_code=400)
        
#         #Get dosen data
#         from app.models.dosen_model import Dosen
#         from schemas.dosen_schema import DosenSchema

#         dosen = Dosen.query.filter_by(user_id=result['user'].id).first()
#         dosen_data = DosenSchema().dump(dosen) if dosen else None

#         response_data = {
#             'access_token' : result['access_token'],
#             'refresh_token': result['refresh_token'],
#             'expires_in' : 3600,
#             'user' : user_schema.dump(result['user']),
#             'dosen':dosen_data
#         }

#         return success_response("Registrasi berhasil! Selamat datang", response_data, 201)
    
#     except ValidationError as e:
#         return error_response("Validation error", e.messages, 400)
#     except Exception as e:
#         print(f"ERROR DI COMPLETE DATA DOSEN : {str(e)}")
#         return error_response("Registrasi gagal", str(e), 500)

@google_auth_bp.route('/google/complete-profile/dosen', methods=['POST'])
def complete_profile_dosen():
    """Complete profile for new dosen after Google login"""
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        # Validate form data
        data = complete_profile_dosen_schema.load(form_data)
        
        # Get signature file if uploaded
        # signature_file = None
        # print(request.files,"files di controler")
        # if 'signature' in request.files:
        #     print("001 MASUK")
        #     signature_file = request.files.get('tanda_tangan')
        #     if signature_file.filename == '':
        #         signature_file = None
        #     else:
        #         # Additional validation for signature file
        #         from utils.file_utils import is_signature_file  # If you add this function
        #         if not is_signature_file(signature_file.filename):
        #             return error_response(
        #                 "File tanda tangan harus berformat PNG, JPG, JPEG, atau GIF",
        #                 status_code=400
        #             )
        signature_file = None
        print("FILES RECEIVED:", request.files)

        # cek dua kemungkinan nama field
        if 'tanda_tangan' in request.files or 'signature' in request.files:
            signature_file = request.files.get('tanda_tangan') or request.files.get('signature')
            print("✅ Signature file diterima:", signature_file.filename)

            if signature_file and signature_file.filename != '':
                from utils.file_utils import is_signature_file
                if not is_signature_file(signature_file.filename):
                    return error_response(
                        "File tanda tangan harus berformat PNG, JPG, JPEG, atau GIF",
                        status_code=400
                    )
            else:
                signature_file = None
        else:
            print("⚠️ Tidak ada file tanda tangan yang dikirim.")
        
        # Verify Google token and get user data
        google_data, error = google_oauth_service.verify_google_token(data['token'])
        if error:
            return error_response(error, status_code=400)
        
        # Create dosen user
        result, error = google_oauth_service.create_dosen_from_google(
            google_data=google_data,
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


@google_auth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """
    Google OAuth callback endpoint (optional, for redirect flow)
    """
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return redirect(f"{FRONTEND_URL}/login?error={error}")
    
    if not code:
        return redirect(f"{FRONTEND_URL}/login?error=no_code")
    
    return redirect(f"{FRONTEND_URL}/auth/google/callback?code={code}")