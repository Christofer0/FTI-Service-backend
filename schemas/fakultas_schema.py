# schemas/fakultas_schema.py
from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.fakultas_model import Fakultas, ProgramStudi
from .base_schema import BaseSchema

class FakultasSchema(SQLAlchemyAutoSchema, BaseSchema):
    """Schema for Fakultas model"""
    class Meta:
        model = Fakultas
        load_instance = True

class ProgramStudiSchema(SQLAlchemyAutoSchema, BaseSchema):
    """Schema for ProgramStudi model"""
    class Meta:
        model = ProgramStudi
        load_instance = True
    
    fakultas = fields.Nested(FakultasSchema, dump_only=True)
