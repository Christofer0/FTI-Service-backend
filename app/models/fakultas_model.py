# models/fakultas_model.py
from extensions import db
from .base_model import BaseModel

class Fakultas(BaseModel):
    __tablename__ = 'fakultas'
    
    id = db.Column(db.Integer, primary_key=True)
    nama_fakultas = db.Column(db.String(255), nullable=False)
    
    # Relationships
    program_studi = db.relationship('ProgramStudi', backref='fakultas', cascade='all, delete-orphan')
    mahasiswa = db.relationship('Mahasiswa', backref='fakultas_mahasiswa')
    dosen = db.relationship('Dosen', backref='fakultas_dosen')
    
    def __repr__(self):
        return f'<Fakultas {self.nama_fakultas}>'
    
    def to_dict(self, with_program_studi=True):
        data = {
            "id": self.id,
            "nama_fakultas": self.nama_fakultas
        }
        if with_program_studi:
            data["program_studi"] = [ps.to_dict() for ps in self.program_studi]
        return data

class ProgramStudi(BaseModel):
    __tablename__ = 'program_studi'
    
    id = db.Column(db.Integer, primary_key=True)
    fakultas_id = db.Column(db.Integer, db.ForeignKey('fakultas.id', ondelete='CASCADE'), nullable=False)
    nama_prodi = db.Column(db.String(255), nullable=False)
    
    # Relationships
    mahasiswa = db.relationship('Mahasiswa', backref='program_studi')
    
    def __repr__(self):
        return f'<ProgramStudi {self.nama_prodi}>'
    
    def to_dict(self):
        return {
            "id": self.id,
            "nama_prodi": self.nama_prodi
        }
