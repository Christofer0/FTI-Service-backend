# models/history_model.py
import uuid
from datetime import datetime
from extensions import db
from .base_model import BaseModel

class History(BaseModel):
    __tablename__ = 'history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    permohonan_id = db.Column(db.String(36), db.ForeignKey('permohonan.id', ondelete='CASCADE'))
    id_jenis_permohonan = db.Column(db.Integer, db.ForeignKey('jenis_permohonan.id'))
    id_mahasiswa = db.Column(db.String(36), db.ForeignKey('mahasiswa.user_id'))
    id_dosen = db.Column(db.String(36), db.ForeignKey('dosen.user_id'))
    action = db.Column(db.String(50), nullable=False)  # 'created', 'approved', 'rejected', 'signed'
    signature_hash = db.Column(db.String(255))
    qr_code_path = db.Column(db.String(255))
    signed_at = db.Column(db.DateTime)
    komentar_permohonan = db.Column(db.Text)
    
    def __repr__(self):
        return f'<History {self.action} - Permohonan {self.permohonan_id}>'
