# schemas/permohonan_schema.py
from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.permohonan_model import Permohonan, JenisPermohonan
from .base_schema import BaseSchema
from .user_schema import UserSchema
from .mahasiswa_schema import MahasiswaSchema
from .dosen_schema import DosenSchema

class JenisPermohonanSchema(SQLAlchemyAutoSchema, BaseSchema):
    """Schema for JenisPermohonan model"""
    class Meta:
        model = JenisPermohonan
        load_instance = True

class PermohonanSchema(SQLAlchemyAutoSchema, BaseSchema):
    """Schema for Permohonan model"""
    class Meta:
        model = Permohonan
        load_instance = True
    
    # Nested relationships
    jenis_permohonan = fields.Nested(JenisPermohonanSchema, dump_only=True)
    mahasiswa = fields.Nested(lambda: MahasiswaSchema(), dump_only=True)
    dosen = fields.Nested(lambda: DosenSchema(), dump_only=True)
    
    # Custom properties
    is_pending = fields.Boolean(dump_only=True)
    is_approved = fields.Boolean(dump_only=True)
    is_rejected = fields.Boolean(dump_only=True)
    is_signed = fields.Boolean(dump_only=True)
    is_completed = fields.Boolean(dump_only=True)

class CreatePermohonanSchema(Schema):
    """Schema for creating permohonan"""
    id_jenis_permohonan = fields.Int(required=True)
    id_dosen = fields.Str(required=True)
    judul = fields.Str(required=True, validate=validate.Length(min=5, max=255))
    deskripsi = fields.Str(allow_none=True)
    file_name = fields.Str(allow_none=True)

class UpdatePermohonanSchema(Schema):
    """Schema for updating permohonan"""
    status_permohonan = fields.Str(
        validate=validate.OneOf(['pending', 'disetujui', 'ditolak', 'ditandatangani', 'selesai']),
        allow_none=True
    )
    komentar = fields.Str(allow_none=True)
    komentar_penolakan = fields.Str(allow_none=True)

class CreateJenisPermohonanSchema(Schema):
    """Schema for creating jenis permohonan"""
    nama_jenis_permohonan = fields.Str(
        required=True, 
        validate=validate.Length(min=3, max=255)
    )
    deskripsi = fields.Str(allow_none=True)
    is_active = fields.Boolean(load_default=True)  # default True


class UpdateJenisPermohonanSchema(Schema):
    """Schema for updating jenis permohonan"""
    nama_jenis_permohonan = fields.Str(
        validate=validate.Length(min=3, max=255)
    )
    deskripsi = fields.Str(allow_none=True)
    is_active = fields.Boolean()

