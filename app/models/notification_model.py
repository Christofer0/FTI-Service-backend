# models/notification_model.py
import uuid
from extensions import db
from .base_model import BaseModel

class Notification(BaseModel):
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    permohonan_id = db.Column(db.String(36), db.ForeignKey('permohonan.id', ondelete='CASCADE'))
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'new_request', 'approved', 'rejected', 'signed'
    is_read = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Notification {self.title} - {self.type}>'