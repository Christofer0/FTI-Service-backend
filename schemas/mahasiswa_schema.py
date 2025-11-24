# schemas/mahasiswa_schema.py
from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.mahasiswa_model import Mahasiswa
from .user_schema import UserSchema
from .fakultas_schema import FakultasSchema, ProgramStudiSchema

class MahasiswaSchema(SQLAlchemyAutoSchema):
    """Schema for Mahasiswa model"""
    class Meta:
        model = Mahasiswa
        load_instance = True
    
    user = fields.Nested(UserSchema, dump_only=True)
    fakultas_mahasiswa = fields.Nested(FakultasSchema, dump_only=True, attribute='fakultas_mahasiswa')
    program_studi = fields.Nested(ProgramStudiSchema, dump_only=True)

