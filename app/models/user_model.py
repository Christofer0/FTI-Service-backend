# models/user_model.py
import uuid
from datetime import datetime
from extensions import db
from .base_model import BaseModel

class User(BaseModel):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nomor_induk = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    nama = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    role = db.Column(db.Enum('admin', 'dosen', 'mahasiswa', name='user_roles'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    no_hp = db.Column(db.String(15),nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    mahasiswa = db.relationship('Mahasiswa', backref='user', uselist=False, cascade='all, delete-orphan')
    dosen = db.relationship('Dosen', backref='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.nama} ({self.nomor_induk})>'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_dosen(self):
        return self.role == 'dosen'
    
    @property
    def is_mahasiswa(self):
        return self.role == 'mahasiswa'
    
    def to_dict(self):
        return {
            "id": self.id,
            "nomor_induk": self.nomor_induk,
            "nama": self.nama,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "no_hp": self.no_hp,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }