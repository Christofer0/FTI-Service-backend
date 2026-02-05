from marshmallow import Schema, fields, validate


class VerifyOTPSchema(Schema):
    """Schema for verifying OTP code"""
    email = fields.Email(required=True)
    otp_code = fields.Str(required=True, validate=validate.Length(equal=6))


class ResendOTPSchema(Schema):
    """Schema for resending OTP"""
    email = fields.Email(required=True)