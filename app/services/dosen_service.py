# services/dosen_service.py
from flask import current_app
from app.repositories.dosen_repository import DosenRepository
from app.repositories.user_repository import UserRepository
from datetime import datetime
from extensions import db
import os

class DosenService:
    def __init__(self):
        self.dosen_repo = DosenRepository()
        self.user_repo = UserRepository()

    def get_all_dosen(self):
        dosen_list = self.dosen_repo.get_all()
        result = []
        for dosen in dosen_list:
            user = self.user_repo.get_by_id(dosen.user_id)
            if user:
                result.append({
                    "id": str(dosen.user_id),
                    "nama": user.nama
                })
        return result

    def upload_signature(self, user_id: str, signature_path: str):
        """Upload signature untuk dosen"""
        try:
            dosen = self.dosen_repo.get_by_user_id(user_id)
            if not dosen:
                return None, "Dosen not found"
            
            # Hapus file lama jika ada
            if dosen.ttd_path:
                old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], dosen.ttd_path)
                if os.path.exists(old_file_path):
                    try:
                        os.remove(old_file_path)
                    except Exception as e:
                        print(f"Failed to delete old signature: {e}")

            # Update path baru
            dosen.ttd_path = signature_path
            dosen.signature_upload_at = datetime.utcnow()
            db.session.commit()
            
            return dosen, None
                
        except Exception as e:
            db.session.rollback()
            return None, str(e)
