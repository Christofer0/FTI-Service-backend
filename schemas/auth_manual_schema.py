from marshmallow import Schema, fields, validate, validates, ValidationError
import re


class CheckEmailSchema(Schema):
    """Schema for checking email eligibility"""
    email = fields.Email(required=True)


class CompleteProfileMahasiswaManualSchema(Schema):
    """Schema for completing mahasiswa profile (manual registration)"""
    email = fields.Email(required=True)
    nama = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    semester = fields.Int(required=True, validate=validate.Range(min=1, max=14))
    no_hp = fields.Str(required=True, validate=validate.Length(min=10, max=15))
    
    @validates('email')
    def validate_mahasiswa_email(self, value, **kwargs):
        print("value: ",value)
        if not value.endswith('@student.uksw.edu'):
            raise ValidationError('Email harus menggunakan domain @student.uksw.edu')


class CompleteProfileAdminManualSchema(Schema):
    """Schema for completing admin profile (manual registration)"""
    email = fields.Email(required=True)
    nama = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    nomor_induk = fields.Str(required=True, validate=validate.Length(min=3, max=20))
    no_hp = fields.Str(required=True, validate=validate.Length(min=10, max=15))
    
    @validates('email')
    def validate_admin_email(self, value, **kwargs):
        if not value.endswith('@uksw.edu'):
            raise ValidationError('Email harus menggunakan domain @uksw.edu')


class CompleteProfileDosenManualSchema(Schema):
    """Schema for completing dosen profile (manual registration)"""
    email = fields.Email(required=True)
    nama = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    nomor_induk = fields.Str(required=True, validate=validate.Length(min=3, max=20))
    no_hp = fields.Str(required=True, validate=validate.Length(min=10, max=15))
    gelar_depan = fields.Str(allow_none=True, validate=validate.Length(max=255))
    gelar_belakang = fields.Str(allow_none=True, validate=validate.Length(max=255))
    jabatan = fields.Str(allow_none=True, validate=validate.Length(max=100))
    fakultas_id = fields.Int(required=True)
    
    @validates('email')
    def validate_dosen_email(self, value, **kwargs):
        if not value.endswith('@uksw.edu'):
            raise ValidationError('Email harus menggunakan domain @uksw.edu')


class LoginManualSchema(Schema):
    """Schema for manual login"""
    nomor_induk = fields.Str(required=True, validate=validate.Length(min=3, max=20))
    password = fields.Str(required=True, validate=validate.Length(min=6))