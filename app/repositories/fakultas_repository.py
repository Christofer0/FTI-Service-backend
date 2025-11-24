from typing import Optional, List
from app.models.fakultas_model import Fakultas, ProgramStudi
from .base_repository import BaseRepository
from sqlalchemy.orm import joinedload

class FakultasRepository(BaseRepository):
    """Repository for Fakultas operations"""
    
    def __init__(self):
        super().__init__(Fakultas)
    
    def get_with_program_studi(self, fakultas_id: int) -> Optional[Fakultas]:
        """Get fakultas with all program studi (1 query)"""
        return self.session.query(Fakultas)\
            .options(joinedload(Fakultas.program_studi))\
            .filter(Fakultas.id == fakultas_id)\
            .first()

    def get_all_with_program_studi(self) -> List[Fakultas]:
        """Get all fakultas with program studi (1 query)"""
        return self.session.query(Fakultas)\
            .options(joinedload(Fakultas.program_studi))\
            .all()
    
class ProgramStudiRepository(BaseRepository):
    """Repository for Program Studi operations"""
    
    def __init__(self):
        super().__init__(ProgramStudi)
    
    def get_by_id(self, prodi_id: int) -> Optional[ProgramStudi]:
        """Get program studi by ID"""
        return self.session.query(ProgramStudi).filter(ProgramStudi.id == prodi_id).first()
