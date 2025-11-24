# models/permohonan_model.py
import uuid
from datetime import datetime
from extensions import db
from .base_model import BaseModel

class JenisPermohonan(BaseModel):
    __tablename__ = 'jenis_permohonan'
    
    id = db.Column(db.Integer, primary_key=True)
    nama_jenis_permohonan = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    # Tambahan: route path untuk mapping ke halaman/form Vue
    route_path = db.Column(db.String(255), nullable=True)

    # Relationships
    permohonan = db.relationship('Permohonan', backref='jenis_permohonan')
    history = db.relationship('History', backref='jenis_permohonan_history')
    
    def __repr__(self):
        return f'<JenisPermohonan {self.nama_jenis_permohonan}>'


class Permohonan(BaseModel):
    __tablename__ = 'permohonan'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_jenis_permohonan = db.Column(db.Integer, db.ForeignKey('jenis_permohonan.id'))
    id_mahasiswa = db.Column(db.String(36), db.ForeignKey('mahasiswa.user_id'))
    id_dosen = db.Column(db.String(36), db.ForeignKey('dosen.user_id'))
    judul = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    file_signed_path = db.Column(db.String(255))
    komentar = db.Column(db.Text)
    komentar_penolakan = db.Column(db.Text)
    qr_code_data = db.Column(db.Text)
    qr_code_path = db.Column(db.String(255))
    status_permohonan = db.Column(
        db.Enum('pending', 'disetujui', 'ditolak', 'ditandatangani', 'selesai', 
               name='status_permohonan_enum'), 
        default='pending'
    )
    approved_at = db.Column(db.DateTime)
    signed_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    
    # Relationships
    history = db.relationship('History', backref='permohonan', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='permohonan', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Permohonan {self.judul} - {self.status_permohonan}>'
    
    @property
    def is_pending(self):
        return self.status_permohonan == 'pending'
    
    @property
    def is_approved(self):
        return self.status_permohonan == 'disetujui'
    
    @property
    def is_rejected(self):
        return self.status_permohonan == 'ditolak'
    
    @property
    def is_signed(self):
        return self.status_permohonan == 'ditandatangani'
    
    @property
    def is_completed(self):
        return self.status_permohonan == 'selesai'

    def to_dict(self):
        """Ubah objek SQLAlchemy menjadi dict JSON-friendly"""
        return {
            "id": self.id,
            "judul": self.judul,
            "status_permohonan": self.status_permohonan,
            "id_dosen": self.id_dosen,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "dosen": {
                "user_id": getattr(self.dosen, "user_id", None),
                "nama": getattr(self.dosen.user, "nama", None)
                if getattr(self.dosen, "user", None)
                else None,
            } if self.dosen else None,
        }
