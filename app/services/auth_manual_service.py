import re
from app.models.user_model import User
from app.models.mahasiswa_model import Mahasiswa
from app.models.dosen_model import Dosen
from app.models.fakultas_model import ProgramStudi
from extensions import db, bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import os
from werkzeug.utils import secure_filename


class AuthManualService:
    """Service for handling manual authentication (non-Google)"""
    
    def check_email_eligibility(self, email):
        """
        Check if email is eligible for registration and determine role
        
        Returns:
            tuple: (result_dict, error_message)
            result_dict contains: role, nomor_induk (if applicable), email, etc.
        """
        try:
            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return None, "Email sudah terdaftar"
            
            # Determine role based on email domain
            if email.endswith('@student.uksw.edu'):
                return self._check_mahasiswa_email(email)
            
            elif email.endswith('@uksw.edu'):
                return self._check_staff_email(email)
            
            else:
                return None, "Email harus menggunakan domain UKSW (@student.uksw.edu atau @uksw.edu)"
        
        except Exception as e:
            return None, f"Error checking email: {str(e)}"
    
    def _check_mahasiswa_email(self, email):
        """Check mahasiswa email eligibility"""
        # Extract NIM from email (9 digits before @)
        match = re.match(r'^(\d+)@student\.uksw\.edu$', email)
        
        if not match:
            return None, "Format email mahasiswa tidak valid"
        
        nim = match.group(1)
        
        # Validate: must be at least 9 digits
        if len(nim) < 9:
            return None, "NIM harus minimal 9 digit"
        
        # Validate: first 2 digits must be "67"
        if not nim.startswith('67'):
            return None, "Hanya mahasiswa dengan NIM yang diawali 67 yang dapat mendaftar"
        
        # Get first 9 digits as nomor_induk
        nomor_induk = nim[:9]
        
        # Get prodi_id from nomor_induk (format: 67PPPPXXX)
        # PP = program studi code (digits 3-4 or 3-6 depending on your system)
        prodi_code = nim[:2]  # Ambil 2 digit setelah "67"
        
        # Find program studi by code
        prodi = ProgramStudi.query.filter_by(id=prodi_code).first()
        
        if not prodi:
            # Try with 2 digits only
            prodi_code = nim[2:4]
            prodi = ProgramStudi.query.filter_by(id=prodi_code).first()
        
        prodi_id = prodi.id if prodi else None
        fakultas_id = prodi.fakultas_id if prodi else None
        
        result = {
            'needs_profile': True,
            'role': 'mahasiswa',
            'nomor_induk': nomor_induk,
            'email': email,
            'prodi_id': prodi_id,
            'fakultas_id': fakultas_id
        }
        
        return result, None
    
    def _check_staff_email(self, email):
        """Check staff email (could be dosen or admin)"""
        # Check if users table is empty -> first user becomes admin
        user_count = User.query.count()
        
        if user_count == 0:
            result = {
                'needs_profile': True,
                'role': 'admin',
                'email': email
            }
            return result, None
        
        # All @uksw.edu emails can register as dosen
        result = {
            'needs_profile': True,
            'role': 'dosen',
            'email': email
        }
        return result, None
    
    def create_mahasiswa_manual(self, email, nama, password, semester, no_hp):
        """Create mahasiswa user from manual registration"""
        try:
            # Re-validate email
            check_result, error = self._check_mahasiswa_email(email)
            if error:
                return None, error
            
            nomor_induk = check_result['nomor_induk']
            prodi_id = check_result['prodi_id']
            fakultas_id = check_result['fakultas_id']
            
            # Hash password
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            
            # Create user
            user = User(
                nomor_induk=nomor_induk,
                password=hashed_password,
                nama=nama,
                email=email,
                role='mahasiswa',
                no_hp=no_hp,
                is_active=True
            )
            
            db.session.add(user)
            db.session.flush()  # Get user.id
            
            # Create mahasiswa record
            mahasiswa = Mahasiswa(
                user_id=user.id,
                fakultas_id=fakultas_id,
                program_studi_id=prodi_id,
                semester=semester
            )
            
            db.session.add(mahasiswa)
            db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'user': user,
                'access_token': access_token,
                'refresh_token': refresh_token
            }, None
            
        except IntegrityError as e:
            db.session.rollback()
            print("EROR: ",e)
            return None, "Nomor induk atau email sudah terdaftar"
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    def create_admin_manual(self, email, nama, password, nomor_induk, no_hp):
        """Create admin user from manual registration"""
        try:
            # Verify this should be admin
            user_count = User.query.count()
            if user_count > 0:
                return None, "Admin sudah ada. Tidak dapat membuat admin baru."
            
            # Hash password
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            
            # Create user
            user = User(
                nomor_induk=nomor_induk,
                password=hashed_password,
                nama=nama,
                email=email,
                role='admin',
                no_hp=no_hp,
                is_active=True
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'user': user,
                'access_token': access_token,
                'refresh_token': refresh_token
            }, None
            
        except IntegrityError:
            db.session.rollback()
            return None, "Nomor induk atau email sudah terdaftar"
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    def create_dosen_manual(self, email, nama, password, nomor_induk, no_hp, 
                           gelar_depan=None, gelar_belakang=None, 
                           jabatan=None, fakultas_id=None, signature_file=None):
        """Create dosen user from manual registration"""
        try:
            # Verify email domain
            if not email.endswith('@uksw.edu'):
                return None, "Email harus menggunakan domain @uksw.edu"
            
            # Hash password
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            
            # Handle signature upload
            ttd_path = None
            if signature_file:
                from utils.file_utils import save_signature_direct
                ttd_path,error = save_signature_direct(signature_file)
            
            if error:
                return None, f"Gagal upload tanda tangan: {error}"
            
            # Create user
            user = User(
                nomor_induk=nomor_induk,
                password=hashed_password,
                nama=nama,
                email=email,
                role='dosen',
                no_hp=no_hp,
                is_active=True
            )
            
            db.session.add(user)
            db.session.flush()  # Get user.id
            
            # Create dosen record
            dosen = Dosen(
                user_id=user.id,
                fakultas_id=fakultas_id,
                gelar_depan=gelar_depan,
                gelar_belakang=gelar_belakang,
                jabatan=jabatan,
                ttd_path=ttd_path,
                signature_upload_at=datetime.utcnow() if ttd_path else None
            )
            
            db.session.add(dosen)
            db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'user': user,
                'access_token': access_token,
                'refresh_token': refresh_token
            }, None
            
        except IntegrityError:
            db.session.rollback()
            return None, "Nomor induk atau email sudah terdaftar"
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    def _save_signature(self, signature_file, nomor_induk):
        """Save signature file and return path"""
        try:
            upload_folder = os.path.join('static', 'signatures')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(signature_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{nomor_induk}_{timestamp}_{filename}"
            
            filepath = os.path.join(upload_folder, filename)
            signature_file.save(filepath)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Failed to save signature: {str(e)}")
    
    def login_manual(self, nomor_induk, password):
        """Manual login with nomor_induk and password"""
        try:
            # Find user by nomor_induk
            user = User.query.filter_by(nomor_induk=nomor_induk).first()
            
            if not user:
                return None, "Nomor induk atau password salah"
            
            # Check password
            if not bcrypt.check_password_hash(user.password, password):
                return None, "Nomor induk atau password salah"
            
            # Check if user is active
            if not user.is_active:
                return None, "Akun Anda tidak aktif. Hubungi administrator."
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'user': user,
                'access_token': access_token,
                'refresh_token': refresh_token
            }, None
            
        except Exception as e:
            return None, str(e)