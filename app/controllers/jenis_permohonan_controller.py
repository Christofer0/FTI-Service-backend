from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.services.jenis_permohonan_service import JenisPermohonanService
from schemas.permohonan_schema import (
    JenisPermohonanSchema,
    CreateJenisPermohonanSchema,
    UpdateJenisPermohonanSchema,
)
from utils.jwt_utils import role_required
from utils.response_utils import success_response, error_response

jenis_permohonan_bp = Blueprint("jenis_permohonan", __name__)
service = JenisPermohonanService()

# Schema instances
schema = JenisPermohonanSchema()
list_schema = JenisPermohonanSchema(many=True)
create_schema = CreateJenisPermohonanSchema()
update_schema = UpdateJenisPermohonanSchema()


@jenis_permohonan_bp.route("/", methods=["GET"])
@jwt_required()
def get_all():
    """Get all jenis permohonan"""
    jenis_list = service.get_all()
    return success_response("List retrieved", list_schema.dump(jenis_list))


@jenis_permohonan_bp.route("/<int:jenis_id>", methods=["GET"])
@jwt_required()
def get_by_id(jenis_id):
    """Get jenis permohonan by ID"""
    jenis = service.get_by_id(jenis_id)
    if not jenis:
        return error_response("Not found", status_code=404)
    return success_response("Detail retrieved", schema.dump(jenis))


@jenis_permohonan_bp.route("/", methods=["POST"])
@role_required("admin")
def create(current_user):
    """Create jenis permohonan (admin only)"""
    try:
        data = create_schema.load(request.json or {})
        jenis, error = service.create(data)
        if error:
            return error_response(error, 400)
        return success_response("Created successfully", schema.dump(jenis), 201)
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)


@jenis_permohonan_bp.route("/<int:jenis_id>", methods=["PUT"])
@role_required("admin")
def update(current_user, jenis_id):
    """Update jenis permohonan (admin only)"""
    try:
        data = update_schema.load(request.json or {})
        jenis, error = service.update(jenis_id, data)
        if error:
            return error_response(error, 400)
        return success_response("Updated successfully", schema.dump(jenis))
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)


@jenis_permohonan_bp.route("/<int:jenis_id>", methods=["DELETE"])
@role_required("admin")
def delete(current_user, jenis_id):
    """Delete jenis permohonan (admin only)"""
    deleted, error = service.delete(jenis_id)
    if error:
        return error_response(error, 400)
    return success_response("Deleted successfully", {"deleted": deleted})
