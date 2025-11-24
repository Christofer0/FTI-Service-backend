# repositories/mahasiswa_repository.py
from typing import Optional, List
from app.models.mahasiswa_model import Mahasiswa
from app.models.user_model import User
from app.models.fakultas_model import Fakultas, ProgramStudi
from .base_repository import BaseRepository

class MahasiswaRepository(BaseRepository):
    """Repository for Mahasiswa operations"""
    
    def __init__(self):
        super().__init__(Mahasiswa)
    
    def get_with_details(self, user_id: str) -> Optional[Mahasiswa]:
        """Get mahasiswa with user, fakultas, and program studi details"""
        return self.session.query(Mahasiswa)\
            .join(User)\
            .join(Fakultas)\
            .join(ProgramStudi)\
            .filter(Mahasiswa.user_id == user_id)\
            .first()
    
    def get_by_fakultas(self, fakultas_id: int) -> List[Mahasiswa]:
        """Get all mahasiswa by fakultas"""
        return self.session.query(Mahasiswa)\
            .filter_by(fakultas_id=fakultas_id)\
            .all()
    
    def get_by_program_studi(self, program_studi_id: int) -> List[Mahasiswa]:
        """Get all mahasiswa by program studi"""
        return self.session.query(Mahasiswa)\
            .filter_by(program_studi_id=program_studi_id)\
            .all()
    
    def get_by_semester(self, semester: int) -> List[Mahasiswa]:
        """Get all mahasiswa by semester"""
        return self.session.query(Mahasiswa)\
            .filter_by(semester=semester)\
            .all()
