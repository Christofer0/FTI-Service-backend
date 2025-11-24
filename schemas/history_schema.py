# schemas/history_schema.py
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.history_model import History
from .base_schema import BaseSchema

class HistorySchema(SQLAlchemyAutoSchema, BaseSchema):
    """Schema for History model"""
    class Meta:
        model = History
        load_instance = True
