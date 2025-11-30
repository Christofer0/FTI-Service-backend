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
    
