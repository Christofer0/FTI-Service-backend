from typing import Optional, List, Tuple
from app.repositories.jenis_permohonan_repository import JenisPermohonanRepository
from app.models.permohonan_model import JenisPermohonan
from extensions import db


class JenisPermohonanService:
    """Service for JenisPermohonan operations"""

    def __init__(self):
        self.repo = JenisPermohonanRepository()

    def get_all(self) -> List[JenisPermohonan]:
        return self.repo.get_all()

    def get_by_id(self, jenis_id: int) -> Optional[JenisPermohonan]:
        return self.repo.get_by_id(jenis_id)

    def get_active(self) -> List[JenisPermohonan]:
        return self.repo.get_active()

    def search(self, keyword: str) -> List[JenisPermohonan]:
        return self.repo.search(keyword)

    def _commit_action(self, func) -> Tuple[Optional[object], Optional[str]]:
        try:
            result = func()
            return result, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    def create(self, data: dict):
        return self._commit_action(
            lambda: self.repo.create(
                nama=data["nama_jenis_permohonan"],
                deskripsi=data.get("deskripsi"),
                is_active=data.get("is_active", True),
            )
        )

    def update(self, jenis_id: int, data: dict):
        return self._commit_action(lambda: self.repo.update(jenis_id, **data))

    def delete(self, jenis_id: int):
        try:
            deleted = self.repo.delete(jenis_id)
            return deleted, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
