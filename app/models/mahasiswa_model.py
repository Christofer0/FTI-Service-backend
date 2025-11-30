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
    