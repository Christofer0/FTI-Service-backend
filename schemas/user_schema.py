# schemas/user_schema.py
from marshmallow import Schema, fields, validate, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.user_model import User
from .base_schema import BaseSchema

class UserSchema(SQLAlchemyAutoSchema, BaseSchema):
    """Schema for User model"""
    class Meta:
        model = User
        load_instance = True
        exclude = ('password',)  # Never expose password
    
    # Custom fields
    is_admin = fields.Boolean(dump_only=True)
    is_dosen = fields.Boolean(dump_only=True)
    is_mahasiswa = fields.Boolean(dump_only=True)

class CreateUserSchema(Schema):
    """Schema for creating user"""
    nomor_induk = fields.Str(required=True, validate=validate.Length(min=3, max=20))
    password = fields.Str(validate=validate.Length(min=6), allow_none=True)
    nama = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    email = fields.Email(required=True)
    role = fields.Str(required=True, validate=validate.OneOf(['admin', 'dosen', 'mahasiswa']))
    no_hp = fields.Str(validate=validate.Length(max=15), allow_none=True)
    is_active = fields.Boolean(load_default=True)
    
    # Additional fields for mahasiswa
    fakultas_id = fields.Int(allow_none=True)
    program_studi_id = fields.Int(allow_none=True)
    semester = fields.Int(validate=validate.Range(min=1, max=14), allow_none=True)
    
    # Additional fields for dosen
    gelar_depan = fields.Str(validate=validate.Length(max=255), allow_none=True)
    gelar_belakang = fields.Str(validate=validate.Length(max=255), allow_none=True)
    jabatan = fields.Str(validate=validate.Length(max=100), allow_none=True)
    ttd_path = fields.Str(allow_none=True)

class UpdateUserSchema(Schema):
    """Schema for updating user"""
    nama = fields.Str(validate=validate.Length(min=2, max=150), allow_none=True)
    email = fields.Email(allow_none=True)
    no_hp = fields.Str(validate=validate.Length(max=15), allow_none=True)
    is_active = fields.Boolean(allow_none=True)
    
    # Additional fields for mahasiswa
    semester = fields.Int(validate=validate.Range(min=1, max=14), allow_none=True)
    
    # Additional fields for dosen
    gelar_depan = fields.Str(validate=validate.Length(max=255), allow_none=True)
    gelar_belakang = fields.Str(validate=validate.Length(max=255), allow_none=True)
    jabatan = fields.Str(validate=validate.Length(max=100), allow_none=True)
    ttd_path = fields.Str(allow_none=True)
