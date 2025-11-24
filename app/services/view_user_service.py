from app.repositories.view_user_repository import ViewRepositoryDosen, ViewRepositoryMahasiswa
from typing import List

class ViewUserService:
    """Service for view user operations"""
    
    def __init__(self):
        self.view_dosen_repo = ViewRepositoryDosen()
        self.view_mahasiswa_repo = ViewRepositoryMahasiswa()
    
    def get_all_dosen(self) -> List:
        """Get all dosen from view"""
        return self.view_dosen_repo.get_all_dosen()
    
    def get_all_mahasiswa(self) -> List:
        """Get all mahasiswa from view"""
        return self.view_mahasiswa_repo.get_all_mahasiswa()