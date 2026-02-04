from flask import Blueprint, request,g
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

def get_current_user_by_role_required():
    current_user = g.current_user
    return current_user

@jenis_permohonan_bp.route("/", methods=["GET"])
@jwt_required()
def get_all():
    """Get all jenis permohonan"""
    try:
        jenis_list = service.get_all()
        return success_response("List retrieved", list_schema.dump(jenis_list))
    except Exception as e:
        return error_response("data retrieved", status_code=404)


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
def create():
    """Create jenis permohonan (admin only)"""
    try:
        current_user = get_current_user_by_role_required()  # konsisten, meski belum dipakai

        data = create_schema.load(request.json or {})
        jenis, error = service.create(data)

        if error:
            return error_response(error, 400)

        return success_response(
            "Created successfully",
            schema.dump(jenis),
            201
        )

    except ValidationError as e:
        return error_response("Jenis Permohonan Gagal Ditambahkan", e.messages, 400)


@jenis_permohonan_bp.route("/<int:jenis_id>/activate", methods=["PATCH"])
@role_required("admin")
def activate(jenis_id):
    """Aktifkan jenis permohonan (admin only)"""
    try:
        current_user = get_current_user_by_role_required()

        jenis, error = service.update(jenis_id, {"is_active": True})
        if error:
            return error_response(error, 400)

        return success_response(
            "Jenis permohonan activated",
            schema.dump(jenis)
        )

    except Exception as e:
        return error_response("Failed to activate", str(e), 500)


@jenis_permohonan_bp.route("/<int:jenis_id>/deactivate", methods=["PATCH"])
@role_required("admin")
def deactivate(jenis_id):
    """Nonaktifkan (soft delete) jenis permohonan (admin only)"""
    try:
        current_user = get_current_user_by_role_required()

        jenis, error = service.update(jenis_id, {"is_active": False})
        if error:
            return error_response(error, 400)

        return success_response(
            "Jenis permohonan deactivated",
            schema.dump(jenis)
        )

    except Exception as e:
        return error_response("Failed to deactivate", str(e), 500)


# @jenis_permohonan_bp.route("/<int:jenis_id>", methods=["PUT"])
# @role_required("admin")
# def update(current_user, jenis_id):
#     """Update jenis permohonan (admin only)"""
#     try:
#         data = update_schema.load(request.json or {})
#         jenis, error = service.update(jenis_id, data)
#         if error:
#             return error_response(error, 400)
#         return success_response("Updated successfully", schema.dump(jenis))
#     except ValidationError as e:
#         return error_response("Validation error", e.messages, 400)


# @jenis_permohonan_bp.route("/<int:jenis_id>", methods=["DELETE"])
# @role_required("admin")
# def delete(current_user, jenis_id):
#     """Delete jenis permohonan (admin only)"""
#     deleted, error = service.delete(jenis_id)
#     if error:
#         return error_response(error, 400)
#     return success_response("Deleted successfully", {"deleted": deleted})
