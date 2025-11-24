# repositories/user_repository.py
from typing import Optional
from app.models.user_model import User
from .base_repository import BaseRepository

class UserRepository(BaseRepository):
    """Repository for User operations"""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_nomor_induk(self, nomor_induk: str) -> Optional[User]:
        """Get user by nomor induk"""
        return self.session.query(User).filter_by(nomor_induk=nomor_induk).first()
    
    def get_count_by_role(self,role: str) ->Optional[User]:
        """Get count by role"""
        return self.session.query(User).filter_by(role=role).count()
        
    def get_all(self, **filters):
        return super().get_all(**filters)
    
    def get_all_by_role(self, role: str):
        """Get all users by role"""
        return self.session.query(User).filter_by(role=role).all()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.session.query(User).filter_by(email=email).first()
    
    def get_active_users(self, role: str = None):
        """Get active users by role"""
        query = self.session.query(User).filter_by(is_active=True)
        if role:
            query = query.filter_by(role=role)
        return query.all()
    
    def get_user_count(self) -> int:
        """Get total user count"""
        return self.session.query(User).count()
    
    def search_users(self, search_term: str, role: str = None):
        """Search users by name or nomor_induk"""
        query = self.session.query(User).filter(
            (User.nama.ilike(f'%{search_term}%')) |
            (User.nomor_induk.ilike(f'%{search_term}%'))
        )
        if role:
            query = query.filter_by(role=role)
        return query.all()
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        from datetime import datetime
        return self.update(user_id, last_login=datetime.utcnow())