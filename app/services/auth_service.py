# services/auth_service.py
from flask import current_app
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from app.repositories.user_repository import UserRepository
from app.repositories.mahasiswa_repository import MahasiswaRepository
from app.repositories.dosen_repository import DosenRepository
from utils.password_utils import hash_password, check_password
from app.models.user_model import User
from app.models.mahasiswa_model import Mahasiswa
from app.models.dosen_model import Dosen
from extensions import db

import requests


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.mahasiswa_repo = MahasiswaRepository()
        self.dosen_repo = DosenRepository()
    
    def login(self, nomor_induk: str, password: str) -> tuple:
        """Authenticate user login"""
        # Get user by nomor induk
        user = self.user_repo.get_by_nomor_induk(nomor_induk)
        
        if not user:
            return None, "User not found"
        
        if not user.is_active:
            return None, "Account is deactivated"
        
        # Check password
        if not check_password(password, user.password):
            return None, "Invalid password"
        
        # Update last login
        self.user_repo.update_last_login(user.id)
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user
        }, None
    
    # login with google
    def login_with_google(self, google_token:str) -> tuple:
        """Authenticate user with Google OAuth"""
        try:
            google_user_info = self._verify_google_token(google_token)

            if not google_user_info:
                return None, "Invalid Google token"
            
            email = google_user_info.get('email')
            google_name = google_user_info.get('name','')

            if not self._is_email_allowed(email):
                allowed_domains = ', '.join(current_app.config['ALLOWED_EMAIL_DOMAINS'])
                return None, f"Email harus menggunakan domain institusi: {allowed_domains}"
            
            user = self.user_repo.get_by_email(email)

            if not user:
                # Deteksi role
                nomor_induk = email.split('@')[0]
                if self.user_repo.get_user_count() == 0:
                    role = 'admin'
                elif nomor_induk.isdigit() and len(nomor_induk) == 9:
                    role = 'mahasiswa'
                else :
                    role ='dosen'
                
                return {
                    'action':'complete_profile',
                    'role':role,
                    'email': email,
                    'nama': google_name
                }
            
            if not user.is_active:
                return None, "Akun dinonaktifkan"
            
            self.user_repo.update_last_login(user.id)

            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user
            }, None

        
        except Exception as e:
            current_app.logger.error(f"Google login error: {str(e)}")
            return None, "Google login failed"
        
    def _verify_google_token(self, token: str) -> dict:
        """Verify Google OAuth token"""
        try:
            # Verify token with Google
            response = requests.get(
                'https://oauth2.googleapis.com/tokeninfo',
                params={'id_token': token},
                timeout=5
            )
            
            if response.status_code != 200:
                return None
            
            user_info = response.json()
            
            # Verify client ID
            client_id = current_app.config.get('GOOGLE_CLIENT_ID')
            if user_info.get('aud') != client_id:
                current_app.logger.error("Invalid Google client ID")
                return None
            
            return user_info
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error verifying Google token: {str(e)}")
            return None
    
    def _is_email_allowed(self, email: str) -> bool:
        """Check if email domain is allowed"""
        allowed_domains = current_app.config.get('ALLOWED_EMAIL_DOMAINS', [])
        
        if not allowed_domains or allowed_domains == ['']:
            return True  # No restrictions
        
        email_domain = email.split('@')[-1].lower()
        return email_domain in [domain.lower().strip() for domain in allowed_domains]
            
    
    def register(self, user_data: dict) -> tuple:
        """Register new user with auto role assignment"""
        try:
            # Check if nomor_induk already exists
            existing_user = self.user_repo.get_by_nomor_induk(user_data['nomor_induk'])
            if existing_user:
                return None, "Nomor induk already exists"
            
            # Check if email already exists
            existing_email = self.user_repo.get_by_email(user_data['email'])
            if existing_email:
                return None, "Email already exists"
            
            # Auto assign role based on user count
            user_count = self.user_repo.get_user_count()
            if user_count == 0:
                # First user becomes admin
                assigned_role = 'admin'
            else:
                # Use provided role or default to mahasiswa
                assigned_role = user_data.get('role', 'mahasiswa')
            
            # Hash password
            user_data['password'] = hash_password(user_data['password'])
            
            # Create user with assigned role
            user = User(
                nomor_induk=user_data['nomor_induk'],
                password=user_data['password'],
                nama=user_data['nama'],
                email=user_data['email'],
                role=assigned_role,  # Use assigned role
                no_hp=user_data.get('no_hp'),
                is_active=user_data.get('is_active', True)
            )
            
            db.session.add(user)
            db.session.flush()  # Get user.id
            
            # Create role-specific record only for non-admin users
            if user.role == 'mahasiswa':
                # Untuk mahasiswa, fakultas_id dan program_studi_id bisa optional saat registrasi
                # Bisa di-set nanti melalui update profile
                mahasiswa = Mahasiswa(
                    user_id=user.id,
                    fakultas_id=user_data.get('fakultas_id'),
                    program_studi_id=user_data.get('program_studi_id'),
                    semester=user_data.get('semester', 1)
                )
                db.session.add(mahasiswa)
            
            elif user.role == 'dosen':
                dosen = Dosen(
                    user_id=user.id,
                    fakultas_id=user_data.get('fakultas_id'),
                    gelar_depan=user_data.get('gelar_depan'),
                    gelar_belakang=user_data.get('gelar_belakang'),
                    jabatan=user_data.get('jabatan'),
                    ttd_path=user_data.get('ttd_path'),
                    signature_upload_at=user_data.get('signature_upload_at')
                )
                db.session.add(dosen)
            
            # Admin tidak perlu tabel tambahan
            
            db.session.commit()
            return user, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    def refresh_token(self, user_id: str) -> tuple:
        """Create new access token"""
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return None, "Invalid user"
        
        access_token = create_access_token(identity=user_id)
        return {'access_token': access_token}, None