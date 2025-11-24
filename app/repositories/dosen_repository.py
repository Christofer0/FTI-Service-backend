# repositories/dosen_repository.py
from typing import Optional, List
from app.models.dosen_model import Dosen
from app.models.user_model import User
from app.models.fakultas_model import Fakultas
from .base_repository import BaseRepository

class DosenRepository(BaseRepository):
    """Repository for Dosen operations"""
    
    def __init__(self):
        super().__init__(Dosen)
    
    def get_with_details(self, user_id: str) -> Optional[Dosen]:
        """Get dosen with user and fakultas details"""
        return self.session.query(Dosen)\
            .join(User)\
            .outerjoin(Fakultas)\
            .filter(Dosen.user_id == user_id)\
            .first()
    
    def get_by_fakultas(self, fakultas_id: int) -> List[Dosen]:
        """Get all dosen by fakultas"""
        return self.session.query(Dosen)\
            .filter_by(fakultas_id=fakultas_id)\
            .all()
    
    def get_by_jabatan(self, jabatan: str) -> List[Dosen]:
        """Get all dosen by jabatan"""
        return self.session.query(Dosen)\
            .filter_by(jabatan=jabatan)\
            .all()
    
    def search_dosen(self, search_term: str) -> List[Dosen]:
        """Search dosen by name or gelar"""
        return self.session.query(Dosen)\
            .join(User)\
            .filter(\
                (User.nama.ilike(f'%{search_term}%')) |\
                (Dosen.gelar_depan.ilike(f'%{search_term}%')) |\
                (Dosen.gelar_belakang.ilike(f'%{search_term}%'))\
            ).all()
    
    def get_all(self) -> List[Dosen]:
        """Get all dosen with user relationship"""
        return (
            self.session.query(Dosen)
            .join(User)
            .all()
        )
    
    def get_by_user_id(self, user_id: str):
        return self.session.query(Dosen).filter_by(user_id=user_id).first()

