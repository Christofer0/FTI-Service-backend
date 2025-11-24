# repositories/permohonan_repository.py
from typing import Optional, List
from datetime import datetime
from sqlalchemy import and_, or_
from app.models.permohonan_model import Permohonan, JenisPermohonan
from app.models.mahasiswa_model import Mahasiswa
from app.models.dosen_model import Dosen
from app.models.user_model import User
from .base_repository import BaseRepository


class PermohonanRepository(BaseRepository):
    """Repository for Permohonan operations"""
    
    def __init__(self):
        super().__init__(Permohonan)
    
    def get_with_details(self, permohonan_id: int) -> Optional[Permohonan]:
        """Get permohonan with all related details"""
        return self.session.query(Permohonan)\
            .join(JenisPermohonan)\
            .join(Mahasiswa)\
            .join(Dosen)\
            .filter(Permohonan.id == permohonan_id)\
            .first()
    
    def get_by_mahasiswa(self, mahasiswa_id: str, status: str = None) -> List[Permohonan]:
        """Get permohonan by mahasiswa"""
        query = self.session.query(Permohonan).filter_by(id_mahasiswa=mahasiswa_id)
        if status:
            query = query.filter_by(status_permohonan=status)
        return query.order_by(Permohonan.created_at.desc()).all()
    
    def get_by_dosen(self, dosen_id: str, status: str = None) -> List[Permohonan]:
        """Get permohonan by dosen"""
        query = self.session.query(Permohonan).filter_by(id_dosen=dosen_id)
        if status:
            query = query.filter_by(status_permohonan=status)
        return query.order_by(Permohonan.created_at.desc()).all()
    
    def get_all_by_dosen(self, dosen_id: str) -> List[Permohonan]:
        """Ambil semua permohonan berdasarkan ID dosen"""
        result = (
        self.session.query(Permohonan)
        .filter(Permohonan.id_dosen == dosen_id)
        .order_by(Permohonan.created_at.desc())
        .all()
    )
        # ubah semua hasil ke dict
        return [r.to_dict() for r in result]
    
    def get_by_status(self, status: str) -> List[Permohonan]:
        """Get permohonan by status"""
        return self.session.query(Permohonan)\
            .filter_by(status_permohonan=status)\
            .order_by(Permohonan.created_at.desc())\
            .all()
    
    def get_pending_by_dosen(self, dosen_id: str) -> List[Permohonan]:
        """Get pending permohonan for specific dosen"""
        return self.get_by_dosen(dosen_id, 'pending')
    
    def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics"""
        from sqlalchemy import func
        
        stats = {}
        
        # Total permohonan by status
        status_counts = self.session.query(
            Permohonan.status_permohonan,
            func.count(Permohonan.id)
        ).group_by(Permohonan.status_permohonan).all()
        
        for status, count in status_counts:
            stats[f'total_{status}'] = count
        
        # Today's permohonan
        today = datetime.utcnow().date()
        stats['permohonan_hari_ini'] = self.session.query(Permohonan)\
            .filter(func.date(Permohonan.created_at) == today).count()
        
        # This month's permohonan
        current_month = datetime.utcnow().replace(day=1)
        stats['permohonan_bulan_ini'] = self.session.query(Permohonan)\
            .filter(Permohonan.created_at >= current_month).count()
        
        return stats
    
    def search_permohonan(self, search_term: str, status: str = None) -> List[Permohonan]:
        """Search permohonan by judul or mahasiswa name"""
        query = self.session.query(Permohonan)\
            .join(Mahasiswa)\
            .join(User)\
            .filter(\
                (Permohonan.judul.ilike(f'%{search_term}%')) |\
                (User.nama.ilike(f'%{search_term}%'))\
            )
        
        if status:
            query = query.filter(Permohonan.status_permohonan == status)
        
        return query.order_by(Permohonan.created_at.desc()).all()
    
    def update_status(self, permohonan_id: int, status: str, **kwargs) -> Optional[Permohonan]:
        """Update permohonan status with timestamp"""
        update_data = {'status_permohonan': status}
        
        # Add timestamp based on status
        if status == 'disetujui':
            update_data['approved_at'] = datetime.utcnow()
        elif status == 'ditolak':
            update_data['rejected_at'] = datetime.utcnow()
        elif status == 'ditandatangani':
            update_data['signed_at'] = datetime.utcnow()
        
        # Add additional data
        update_data.update(kwargs)
        
        return self.update(permohonan_id, **update_data)
    
    def get_by_dosen_with_filter(self, dosen_id: str, status: str = None, jenis_id: int = None) -> List[Permohonan]:
        """Get permohonan for dosen with optional status & jenis filter"""
        query = self.session.query(Permohonan)\
            .join(Mahasiswa, Permohonan.id_mahasiswa == Mahasiswa.user_id)\
            .join(User, Mahasiswa.user_id == User.id)\
            .join(JenisPermohonan, Permohonan.id_jenis_permohonan == JenisPermohonan.id)\
            .filter(Permohonan.id_dosen == dosen_id)
        
        if status:
            query = query.filter(Permohonan.status_permohonan == status)
        if jenis_id:
            query = query.filter(Permohonan.id_jenis_permohonan == jenis_id)
        
        return query.order_by(Permohonan.created_at.desc()).all()
    
    def get_all_permohonan(self):
        permohonan_list = self.get_all()
        print("DATA DARI DB:", permohonan_list)
        return permohonan_list
        

    
    
    


