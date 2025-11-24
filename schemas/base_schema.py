# schemas/base_schema.py
from marshmallow import Schema, fields, validate

class BaseSchema(Schema):
    """Base schema with common fields"""
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)