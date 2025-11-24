# repositories/jenis_permohonan_repository.py
from typing import Optional, List
from app.models.permohonan_model import JenisPermohonan
from .base_repository import BaseRepository
from sqlalchemy import or_

class JenisPermohonanRepository(BaseRepository):
    """Repository for JenisPermohonan operations"""
    
    def __init__(self):
        super().__init__(JenisPermohonan)
    
    def get_all(self) -> List[JenisPermohonan]:
        """Get all jenis permohonan"""
        return self.session.query(JenisPermohonan).all()
    
    def get_active(self) -> List[JenisPermohonan]:
        """Get only active jenis permohonan"""
        return self.session.query(JenisPermohonan)\
            .filter_by(is_active=True)\
            .all()
    
    def get_by_id(self, jenis_id: int) -> Optional[JenisPermohonan]:
        """Get jenis permohonan by id"""
        return self.session.query(JenisPermohonan)\
            .filter_by(id=jenis_id)\
            .first()
    
    def search(self, keyword: str) -> List[JenisPermohonan]:
        """Search jenis permohonan by nama or deskripsi"""
        return self.session.query(JenisPermohonan)\
            .filter(or_(
                JenisPermohonan.nama_jenis_permohonan.ilike(f"%{keyword}%"),
                JenisPermohonan.deskripsi.ilike(f"%{keyword}%")
            )).all()
    
    def create(self, nama: str, deskripsi: str = None, is_active: bool = True) -> JenisPermohonan:
        """Create new jenis permohonan"""
        new_jenis = JenisPermohonan(
            nama_jenis_permohonan=nama,
            deskripsi=deskripsi,
            is_active=is_active
        )
        self.session.add(new_jenis)
        self.session.commit()
        return new_jenis
    
    def update(self, jenis_id: int, **kwargs) -> Optional[JenisPermohonan]:
        """Update jenis permohonan"""
        jenis = self.get_by_id(jenis_id)
        if not jenis:
            return None
        for key, value in kwargs.items():
            setattr(jenis, key, value)
        self.session.commit()
        return jenis
    
    def delete(self, jenis_id: int) -> bool:
        """Delete jenis permohonan"""
        jenis = self.get_by_id(jenis_id)
        if not jenis:
            return False
        self.session.delete(jenis)
        self.session.commit()
        return True
