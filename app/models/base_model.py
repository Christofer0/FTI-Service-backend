# models/base_model.py
from datetime import datetime
from extensions import db

class BaseModel(db.Model):
    """Base model with common fields"""
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

