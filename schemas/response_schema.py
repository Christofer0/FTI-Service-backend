# schemas/response_schema.py
from marshmallow import Schema, fields

class SuccessResponseSchema(Schema):
    """Schema for success response"""
    success = fields.Boolean(required=True, default=True)
    message = fields.Str(required=True)
    data = fields.Raw(allow_none=True)

class ErrorResponseSchema(Schema):
    """Schema for error response"""
    success = fields.Boolean(required=True, default=False)
    message = fields.Str(required=True)
    errors = fields.Dict(allow_none=True)

class PaginationSchema(Schema):
    """Schema for pagination metadata"""
    page = fields.Int(required=True)
    per_page = fields.Int(required=True)
    pages = fields.Int(required=True)
    total = fields.Int(required=True)
    has_next = fields.Boolean(required=True)
    has_prev = fields.Boolean(required=True)

class PaginatedResponseSchema(Schema):
    """Schema for paginated response"""
    success = fields.Boolean(required=True, default=True)
    message = fields.Str(required=True)
    data = fields.List(fields.Raw(), required=True)
    pagination = fields.Nested(PaginationSchema, required=True)