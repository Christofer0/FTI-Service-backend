# services/user_service.py
from .base_service import BaseService
from app.repositories.user_repository import UserRepository
from app.repositories.mahasiswa_repository import MahasiswaRepository
from app.repositories.dosen_repository import DosenRepository
from utils.password_utils import hash_password
from extensions import db
from typing import List

class UserService(BaseService):
    """Service for user operations"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.mahasiswa_repo = MahasiswaRepository()
        self.dosen_repo = DosenRepository()
    
    def get_user_profile(self, user_id: str):
        """Get user profile with role-specific data"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None, "User not found"
        
        profile_data = {
            'user': user,
            'role_data': None
        }
        
        if user.role == 'mahasiswa':
            profile_data['role_data'] = self.mahasiswa_repo.get_with_details(user_id)
        elif user.role == 'dosen':
            profile_data['role_data'] = self.dosen_repo.get_with_details(user_id)
        
        return profile_data, None
    
    def get_all(self):
        return self.user_repo.get_all(), None
    
    def get_all_by_role(self, role: str) -> List:
        return self.user_repo.get_all_by_role(role), None
    
    def update_user_profile(self, user_id: str, update_data: dict):
        """Update user profile"""
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return None, "User not found"
            
            # Update user data
            user_fields = ['nama', 'email', 'no_hp']
            user_updates = {k: v for k, v in update_data.items() if k in user_fields}
            
            if user_updates:
                for key, value in user_updates.items():
                    setattr(user, key, value)
            
            # Update role-specific data
            if user.role == 'mahasiswa' and user.mahasiswa:
                mahasiswa_fields = ['semester']
                mahasiswa_updates = {k: v for k, v in update_data.items() if k in mahasiswa_fields}
                
                for key, value in mahasiswa_updates.items():
                    setattr(user.mahasiswa, key, value)
            
            elif user.role == 'dosen' and user.dosen:
                dosen_fields = ['gelar_depan', 'gelar_belakang', 'jabatan']
                dosen_updates = {k: v for k, v in update_data.items() if k in dosen_fields}
                
                for key, value in dosen_updates.items():
                    setattr(user.dosen, key, value)
            
            db.session.commit()
            return user, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    def change_password(self, user_id: str, old_password: str, new_password: str):
        """Change user password"""
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return False, "User not found"
            
            from utils.password_utils import check_password
            if not check_password(old_password, user.password):
                return False, "Current password is incorrect"
            
            user.password = hash_password(new_password)
            db.session.commit()
            return True, "Password changed successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def upload_signature(self, user_id: str, signature_path: str):
        """Upload user signature"""
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return None, "User not found"
            
            from datetime import datetime
            user.ttd_path = signature_path
            user.signature_upload_at = datetime.utcnow()
            db.session.commit()
            
            return user, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
        
    def toggle_status(self, user_id: str, action: str):
        """Toggle user active status"""
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return False, "User not found"
            if action not in ['activate', 'deactivate']:
                return False, "Invalid action"
            if action == 'activate':
                user.is_active = True
            elif action == 'deactivate':
                user.is_active = False
            db.session.commit()
            return True, "User status toggled successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
