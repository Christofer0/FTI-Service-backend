# schemas/auth_schema.py
from marshmallow import Schema, fields, validate
from .user_schema import CreateUserSchema, UserSchema

class LoginSchema(Schema):
    """Schema for user login"""
    nomor_induk = fields.Str(required=True, validate=validate.Length(min=3, max=20))
    password = fields.Str(required=True, validate=validate.Length(min=6))

class RegisterSchema(CreateUserSchema):
    """Schema for user registration (extends CreateUserSchema)"""
    # Logic auto role ada di service layer, bukan di schema
    pass

class RefreshTokenSchema(Schema):
    """Schema for refresh token"""
    refresh_token = fields.Str(required=True)

class TokenResponseSchema(Schema):
    """Schema for token response"""
    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=True)
    expires_in = fields.Int(required=True)
    user = fields.Nested(UserSchema, required=True)