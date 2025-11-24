# models/dosen_model.py
from extensions import db
from datetime import datetime

class Dosen(db.Model):
    __tablename__ = 'dosen'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    fakultas_id = db.Column(db.Integer, db.ForeignKey('fakultas.id'))
    gelar_depan = db.Column(db.String(255))
    gelar_belakang = db.Column(db.String(255))
    jabatan = db.Column(db.String(100))
    ttd_path = db.Column(db.String(255))
    signature_upload_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Relationships
    permohonan = db.relationship('Permohonan', backref='dosen')
    history = db.relationship('History', backref='dosen_history')
    
    def __repr__(self):
        return f'<Dosen {self.user.nama}>'
    
    @property
    def nama_lengkap(self):
        """Get full name with titles"""
        nama_parts = []
        if self.gelar_depan:
            nama_parts.append(self.gelar_depan)
        nama_parts.append(self.user.nama)
        if self.gelar_belakang:
            nama_parts.append(self.gelar_belakang)
        return ' '.join(nama_parts)
    
    
class ViewDosen(db.Model):
    __tablename__ = 'v_dosen'
    __table_args__ = {'extend_existing': True}
    
    user_id = db.Column(db.String(36), primary_key=True)
    nomor_induk = db.Column(db.String(20))
    nama = db.Column(db.String(100))
    email = db.Column(db.String(100))
    no_hp = db.Column(db.String(15))
    is_active = db.Column(db.Boolean)
    gelar_depan = db.Column(db.String(255))
    gelar_belakang = db.Column(db.String(255))
    nama_lengkap = db.Column(db.String(255))
    jabatan = db.Column(db.String(100))
    fakultas_id = db.Column(db.Integer)
    nama_fakultas = db.Column(db.String(100))
    ttd_path = db.Column(db.String(255))
    signature_upload_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ViewDosen {self.nama}>'
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "nomor_induk": self.nomor_induk,
            "nama": self.nama,
            "email": self.email,
            "no_hp": self.no_hp,
            "is_active": self.is_active,
            "gelar_depan": self.gelar_depan,
            "gelar_belakang": self.gelar_belakang,
            "nama_lengkap": self.nama_lengkap,
            "jabatan": self.jabatan,
            "fakultas_id": self.fakultas_id,
            "nama_fakultas": self.nama_fakultas,
            "ttd_path": self.ttd_path,
            "signature_upload_at": self.signature_upload_at,
            "created_at": self.created_at,
            "last_login": self.last_login
        }