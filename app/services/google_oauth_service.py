# services/google_oauth_service.py
import os , datetime
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from flask_jwt_extended import create_access_token, create_refresh_token

from app.repositories.user_repository import UserRepository
from app.repositories.mahasiswa_repository import MahasiswaRepository
from app.repositories.dosen_repository import DosenRepository
from app.repositories.fakultas_repository import ProgramStudiRepository
from app.models.user_model import User


class GoogleOAuthService:
    """Service for Google OAuth operations"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.mahasiswa_repo = MahasiswaRepository()
        self.prodi_repo = ProgramStudiRepository()
        self.dosen_repo = DosenRepository()
        self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
    
    def verify_google_token(self, token: str) -> dict:
        """Verify Google OAuth token and return user info"""
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                self.google_client_id
            )
            
            # Token is valid, return user info
            return {
                'email': idinfo.get('email'),
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'email_verified': idinfo.get('email_verified', False)
            }, None
            
        except ValueError as e:
            return None, f"Invalid token: {str(e)}"
        except Exception as e:
            return None, f"Token verification failed: {str(e)}"
    
    def determine_role_from_email(self, email: str) -> tuple:
        """
        Determine role based on email domain
        Returns: (role, nomor_induk, prodi_id, error)
        """
        # jangan lupa buka
        if not email.endswith('@uksw.edu') and not email.endswith('@student.uksw.edu'):
            return None, None, None, "Email harus menggunakan domain @uksw.edu atau @student.uksw.edu"
        
        # Check if this is the first user (will be admin)
        user_count = self.user_repo.get_user_count()
        
        if user_count == 0:
            # First user is admin
            return 'admin', None, None, None
        
        # Mahasiswa: email format 672022224@student.uksw.edu
        if '@student.uksw.edu' in email:
            nomor_induk = email.split('@')[0]
            print(nomor_induk,"nomor induk setelah split")
            # Validate nomor induk length (should be at least 3 chars: 2 for prodi + 1 for NIM)
            if len(nomor_induk) < 3:
                return None, None, None, "Format NIM tidak valid"
            
            # Extract prodi_id from first 2 digits
            try:
                prodi_id = int(nomor_induk[:2])
            except ValueError:
                return None, None, None, "Format NIM tidak valid, 2 digit pertama harus angka"
            
            # Validate prodi exists
            prodi = self.prodi_repo.get_by_id(prodi_id)
            if not prodi:
                return None, None, None, f"Program studi dengan ID {prodi_id} tidak ditemukan. Silakan hubungi admin."
            
            return 'mahasiswa', nomor_induk, prodi_id, None
        
        # Dosen: email format jefry@uksw.edu
        # JANGAN LUPA GANTI INI YA !!!!!!!!
        # elif '@uksw.edu' in email:
        elif '@gmail.com' in email:
            return 'dosen', None, None, None
        
        return None, None, None, "Format email tidak valid"
    
    def process_google_login(self, google_token: str) -> tuple:
        """
        Process Google login
        Returns: (result_dict, error)
        
        result_dict contains:
        - needs_profile: True if user needs to complete profile
        - access_token, refresh_token: if user already exists
        - user: user object
        - google_data: data from Google (for profile completion)
        """
        # Verify Google token
        google_data, error = self.verify_google_token(google_token)
        if error:
            return None, error
        
        email = google_data['email']
        
        # Check if user already exists
        existing_user = self.user_repo.get_by_email(email)
        
        if existing_user:
            # User exists, just login
            if not existing_user.is_active:
                return None, "Akun Anda tidak aktif"
            
            # Update last login
            self.user_repo.update_last_login(existing_user.id)
            
            # Create tokens
            access_token = create_access_token(identity=str(existing_user.id))
            refresh_token = create_refresh_token(identity=str(existing_user.id))

            return {
                'needs_profile': False,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': existing_user
            }, None
        
        # User doesn't exist, determine role and check if they need to complete profile
        role, nomor_induk, prodi_id, error = self.determine_role_from_email(email)
        if error:
            return None, error
        
        # For mahasiswa, they need to complete profile
        if role == 'mahasiswa':
            return {
                'needs_profile': True,
                'role': role,
                'nomor_induk': nomor_induk,
                'fakultas_id': 1,  # Default fakultas ID = 1
                'program_studi_id_id': prodi_id,
                'google_data': google_data
            }, None
        
        # For admin and dosen, they also need to complete profile
        # But we'll handle them differently later
        elif role == 'admin':
            return {
                'needs_profile': True,
                'role': role,
                'google_data': google_data
            }, None
        
        elif role == 'dosen':
            return {
                'needs_profile' : True,
                'role' : role,
                'fakultas_id' : 1, #default
                'google_data':google_data
            }, None
        
        else:
            None, "Who Are You ? "

    
    def create_mahasiswa_from_google(self, google_data: dict, semester: int, no_hp: str) -> tuple:
        """
        Create new mahasiswa user from Google data
        Returns: (result_dict, error)
        """
        email = google_data['email']
        name = google_data['name']
        
        # Determine role and extract data
        role, nomor_induk, prodi_id, error = self.determine_role_from_email(email)
        if error:
            return None, error
        
        if role != 'mahasiswa':
            return None, "Email ini bukan untuk mahasiswa"
        
        # Validate prodi exists again (double check)
        prodi = self.prodi_repo.get_by_id(prodi_id)
        if not prodi:
            return None, f"Program studi dengan ID {prodi_id} tidak ditemukan"
        
        try:
            # Create user with dummy password (won't be used for Google login)
            # from utils.security_utils import hash_password
            import secrets
            
            user_data = {
                'nomor_induk': nomor_induk,
                # 'password': hash_password(secrets.token_urlsafe(32)),  # Random secure password
                'password': '',
                'nama': name,
                'email': email,
                'role': 'mahasiswa',
                'is_active': True,
                'no_hp': no_hp
            }
            
            # Create user
            user = self.user_repo.create(**user_data)
            
            # Create mahasiswa record
            mahasiswa_data = {
                'user_id': user.id,
                'fakultas_id': 1,  # Default fakultas ID = 1
                'program_studi_id': prodi_id,
                'semester': semester
            }
            
            mahasiswa = self.mahasiswa_repo.create(**mahasiswa_data)
            
            # Update last login
            self.user_repo.update_last_login(user.id)
            
            # Create tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user,
                'mahasiswa': mahasiswa
            }, None
            
        except Exception as e:
            return None, f"Gagal membuat akun: {str(e)}"
        
    def create_admin_from_google(self, google_data: dict, nomor_induk: str, no_hp: str) -> tuple:
        """
        Create new admin user from Google data
        Returns: (result_dict, error)
        """
        email = google_data['email']
        name = google_data['name']
        # ===========================
        #           PENTING
        # ===========================
        # Validate email domain
        # JANGAN LUPA DIBUKA
        # if not email.endswith('@uksw.edu'):
        #     return None, "Email admin harus menggunakan domain @uksw.edu"
        
        # Check if user already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            return None, "Email sudah terdaftar"
        
        # Check if nomor_induk already exists
        existing_nomor_induk = self.user_repo.get_by_nomor_induk(nomor_induk)
        if existing_nomor_induk:
            return None, "Nomor induk sudah digunakan"
        
        try:
            # Create user with dummy password (won't be used for Google login)
            # from utils.password_utils import hash_password
            # import secrets
            
            user_data = {
                'nomor_induk': nomor_induk,
                # 'password': hash_password(secrets.token_urlsafe(32)),  # Random secure password
                'password':'',
                'nama': name,
                'email': email,
                'role': 'admin',
                'is_active': True,
                'no_hp': no_hp
            }
            
            # Create user
            user = self.user_repo.create(**user_data)
            
            # Update last login
            self.user_repo.update_last_login(user.id)
            
            # Create tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user
            }, None
            
        except Exception as e:
            return None, f"Gagal membuat akun: {str(e)}"
        

    # def create_dosen_from_google(self, google_data: dict, nomor_induk: str,no_hp:str, gelar_depan: str, gelar_belakang:str, jabatan:str, fakultas_id:int, signature_file:None ) -> tuple:
    #     """
    #     Create new admin user from Google data
    #     Returns: (result_dict, error)
    #     """
    #     email = google_data['email']
    #     name = google_data['name']
        
    #     #jangna lupa dibuka
    #     # if not email.endswith('@uksw.edu'):
    #     #     return None, "Email harus menggunakan domain @uksw.edu"
        
    #     #Check User
    #     existing_user = self.user_repo.get_by_email(email)
    #     if existing_user:
    #         return None, "Email sudah terdaftar"
        
    #     #Check if nomor_induk ada
    #     existing_nomor_induk = self.user_repo.get_by_nomor_induk(nomor_induk)
    #     if existing_nomor_induk:
    #         return None, "Nomor Induk sudah ada"
        
    #     try:
    #         # buka jika ingin menambhaknan random password
    #         # import secrets
    #         # from utils.password_utils import hash_password

    #         ttd_path = None
    #         if signature_file:
    #             from utils.file_utils import save_and_resize_signature
    #             ttd_path, error = save_and_resize_signature(signature_file, targer_size = (724,344))

    #             if error:
    #                 return None, f"Gagal mengupload tanda tangan : {error}"
                        
    #         user_data = {
    #             'nomor_induk': nomor_induk,
    #             # 'password':hash_password(secrets.token_urlsafe(32)),
    #             'password':'',
    #             'nama' : name,
    #             'email':email,
    #             'role': 'dosen',
    #             'is_active': True,
    #             'no_hp': no_hp,
    #         }

    #         # create data
    #         user = self.user_repo.create(**user_data)

    #         #Create dosen record
    #         dosen_data = {
    #             'user_id': user.id,
    #             'fakultas_id': 1,
    #             'gelar_depan':gelar_depan if gelar_depan else None,
    #             'gelar_belakang':gelar_belakang if gelar_belakang else None,
    #             'jabatan':jabatan if jabatan else None,
    #             'ttd_path':ttd_path,
    #             'signature_upload_at':datetime.utcnow() if ttd_path else None
    #         }
            
    #         dosen = self.dosen_repo.create(**dosen_data)

    #         #Update last_login
    #         self.user_repo.update_last_login(user.id)

    #         # TOKEN
    #         access_token = create_access_token(identity=str(user.id))
    #         refresh_token = create_refresh_token(identity=str(user.id))

    #         return {
    #             'access_token': access_token,
    #             'refresh_token':refresh_token,
    #             'user':user,
    #             'dosen':dosen
    #         }, None
        
    #     except Exception as e:
    #         return None, f"Gagal membuat akun dosen : {str(e)}" 

    def create_dosen_from_google(
    self, 
    google_data: dict, 
    nomor_induk: str,
    no_hp: str, 
    gelar_depan: str, 
    gelar_belakang: str, 
    jabatan: str, 
    fakultas_id: int,
    signature_file=None  # File object dari Flask request.files
) -> tuple:
        """
        Create new dosen user from Google data
        Returns: (result_dict, error)
        """
        email = google_data['email']
        name = google_data['name']
        
        # Validate email domain
        # JANGAN LUPA BUKA ini
        # if not email.endswith('@uksw.edu'):  
        #     return None, "Email dosen harus menggunakan domain @uksw.edu"
        
        # Check if user already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            return None, "Email sudah terdaftar"
        
        # Check if nomor_induk already exists
        existing_nomor_induk = self.user_repo.get_by_nomor_induk(nomor_induk)
        if existing_nomor_induk:
            return None, "Nomor induk sudah digunakan"
        
        try:
            # from utils.security_utils import hash_password
            # import secrets
            
            # Process signature upload if provided
            # ttd_path = None
            # if signature_file:
            #     from utils.file_utils import save_and_resize_signature
            #     ttd_path, error = save_and_resize_signature(signature_file, target_size=(724, 344))
            #     if error:
            #         return None, f"Gagal upload tanda tangan: {error}"
            ttd_path = None
            if signature_file:
            # ✅ OPTION A: Save direct (jika dari editor frontend)
                from utils.file_utils import save_signature_direct
                ttd_path, error = save_signature_direct(signature_file)
            
            # ✅ OPTION B: Resize (jika upload manual tanpa editor)
                # from utils.file_utils import save_and_resize_signature
                # ttd_path, error = save_and_resize_signature(signature_file, target_size=(724, 344))
            
            if error:
                return None, f"Gagal upload tanda tangan: {error}"
            
            # Create user
            user_data = {
                'nomor_induk': nomor_induk,
                # 'password': hash_password(secrets.token_urlsafe(32)),  # Random secure password
                'password':'',
                'nama': name,
                'email': email,
                'role': 'dosen',
                'is_active': True,
                'no_hp': no_hp,
            }
            
            user = self.user_repo.create(**user_data)
            
            # Create dosen record
            dosen_data = {
                'user_id': user.id,
                'fakultas_id': fakultas_id,
                'gelar_depan': gelar_depan if gelar_depan else None,
                'gelar_belakang': gelar_belakang if gelar_belakang else None,
                'jabatan': jabatan if jabatan else None,
                'ttd_path': ttd_path,
                'signature_upload_at': datetime.datetime.now(datetime.timezone.utc) if ttd_path else None
            }
            
            dosen = self.dosen_repo.create(**dosen_data)
            
            # Update last login
            self.user_repo.update_last_login(user.id)
            
            # Create tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user,
                'dosen': dosen
            }, None
            
        except Exception as e:
            return None, f"Gagal membuat akun dosen: {str(e)}"
        
"""
def create_dosen_from_google(
    self, 
    google_data: dict, 
    nomor_induk: str,
    no_hp: str, 
    gelar_depan: str, 
    gelar_belakang: str, 
    jabatan: str, 
    fakultas_id: int,
    signature_file=None
) -> tuple:
    # ... existing code ...
    
    try:
        # Process signature upload if provided
        ttd_path = None
        if signature_file:
            # ✅ OPTION A: Save direct (jika dari editor frontend)
            from utils.file_utils import save_signature_direct
            ttd_path, error = save_signature_direct(signature_file)
            
            # ✅ OPTION B: Resize (jika upload manual tanpa editor)
            # from utils.file_utils import save_and_resize_signature
            # ttd_path, error = save_and_resize_signature(signature_file, target_size=(724, 344))
            
            if error:
                return None, f"Gagal upload tanda tangan: {error}"
        
        # ... rest of code ...
"""    

