# schemas/notification_schema.py
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.notification_model import Notification
from .base_schema import BaseSchema

class NotificationSchema(SQLAlchemyAutoSchema, BaseSchema):
    """Schema for Notification model"""
    class Meta:
        model = Notification
        load_instance = True
