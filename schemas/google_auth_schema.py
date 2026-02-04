from marshmallow import ValidationError, Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

# Validation Schemas
class GoogleTokenSchema(Schema):
    """Schema for Google token validation"""
    token = fields.Str(required=True)


class CompleteProfileMahasiswaSchema(Schema):
    """Schema for completing mahasiswa profile"""
    token = fields.Str(required=True)  # Google token
    semester = fields.Int(required=True, validate=lambda x: 1 <= x <= 14)
    no_hp = fields.Str(required=True)
    password = fields.Str(required=True)

class CompleteProfileAdminSchema(Schema):
    """Schema for completing admin profile"""
    token = fields.Str(required=True)
    nomor_induk = fields.Str(required=True)
    no_hp = fields.Str(required=True)
    password = fields.Str(required=True)


class CompleteProfileDosenSchema(Schema):
    """Schema for completing dosen profile"""
    token = fields.Str(required=True)
    nomor_induk = fields.Str(required=True)
    no_hp = fields.Str(required=True)
    password = fields.Str(required=True)
    gelar_depan = fields.Str(required=False, allow_none=True)
    gelar_belakang = fields.Str(required=False, allow_none=True)
    jabatan = fields.Str(required=False, allow_none=True)
    fakultas_id = fields.Int(required=True)