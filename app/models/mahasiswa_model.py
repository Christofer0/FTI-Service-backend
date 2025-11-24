# models/mahasiswa_model.py
from extensions import db

class Mahasiswa(db.Model):
    __tablename__ = 'mahasiswa'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    fakultas_id = db.Column(db.Integer, db.ForeignKey('fakultas.id'), nullable=False)
    program_studi_id = db.Column(db.Integer, db.ForeignKey('program_studi.id'), nullable=False)
    semester = db.Column(db.Integer, db.CheckConstraint('semester >= 1 AND semester <= 14'), nullable=False)
    
    # Relationships
    permohonan = db.relationship('Permohonan', backref='mahasiswa')
    history = db.relationship('History', backref='mahasiswa_history')
    
    def __repr__(self):
        return f'<Mahasiswa {self.user.nama}>'
    
class ViewMahasiswa(db.Model):
    __tablename__ = 'v_mahasiswa'
    __table_args__ = {'extend_existing': True}
    
    user_id = db.Column(db.String(36), primary_key=True)
    nomor_induk = db.Column(db.String(20))
    nama = db.Column(db.String(100))
    email = db.Column(db.String(100))
    no_hp = db.Column(db.String(15))
    is_active = db.Column(db.Boolean)
    semester = db.Column(db.Integer)
    fakultas_id = db.Column(db.Integer)
    nama_fakultas = db.Column(db.String(100))
    program_studi_id = db.Column(db.Integer)
    nama_prodi = db.Column(db.String(100))
    created_at = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ViewMahasiswa {self.nama}>'
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "nomor_induk": self.nomor_induk,
            "nama": self.nama,
            "email": self.email,
            "no_hp": self.no_hp,
            "is_active": self.is_active,
            "semester": self.semester,
            "fakultas_id": self.fakultas_id,
            "nama_fakultas": self.nama_fakultas,
            "program_studi_id": self.program_studi_id,
            "nama_prodi": self.nama_prodi,
            "created_at": self.created_at,
            "last_login": self.last_login
        }