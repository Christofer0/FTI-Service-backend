from app.models.dosen_model import  ViewDosen
from app.models.mahasiswa_model import  ViewMahasiswa
from .base_repository import BaseRepository

class ViewRepositoryDosen(BaseRepository):
    """Repository for ViewDosen operations"""
    
    def __init__(self):
        super().__init__(ViewDosen)
    
    def get_all_dosen(self, **filters):
        return super().get_all(**filters)
    
class ViewRepositoryMahasiswa(BaseRepository):
    """Repository for ViewMahasiswa operations"""
    
    def __init__(self):
        super().__init__(ViewMahasiswa)
    
    # def get_all_mahasiswa(self, **filters):
    #     return super().get_all(**filters)
    
