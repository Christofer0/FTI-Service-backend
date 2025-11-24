# schemas/dosen_schema.py
from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.dosen_model import Dosen
from .user_schema import UserSchema
from .fakultas_schema import FakultasSchema

class DosenSchema(SQLAlchemyAutoSchema):
    """Schema for Dosen model"""
    class Meta:
        model = Dosen
        load_instance = True
        include_fk = True
    
    user = fields.Nested(UserSchema, dump_only=True)
    fakultas_dosen = fields.Nested(FakultasSchema, dump_only=True, attribute='fakultas_dosen')
    nama_lengkap = fields.Str(dump_only=True)
    ttd_path = fields.Str(allow_none=True)



