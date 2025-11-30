# controllers/permohonan_controller.py
from flask import Blueprint, request,g
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.services.permohonan_service import PermohonanService
from schemas.permohonan_schema import PermohonanSchema, CreatePermohonanSchema, UpdatePermohonanSchema
from utils.jwt_utils import role_required
from utils.response_utils import success_response, error_response, paginated_response
from utils.file_utils import save_uploaded_file
import traceback

permohonan_bp = Blueprint('permohonan', __name__)
permohonan_service = PermohonanService()

# Schema instances
permohonan_schema = PermohonanSchema()
permohonan_list_schema = PermohonanSchema(many=True)
create_permohonan_schema = CreatePermohonanSchema()
update_permohonan_schema = UpdatePermohonanSchema()

def get_current_user_by_role_required():
    current_user = g.current_user
    return current_user

@permohonan_bp.route('/', methods=['POST'])
@role_required('mahasiswa')
def create_permohonan():
    """Create new permohonan (mahasiswa only)"""
    try:
        current_user = get_current_user_by_role_required() 
        # Get form data
        form_data = request.form.to_dict()

        # Validate form data
        permohonan_data = create_permohonan_schema.load(form_data)
        
        # Handle file upload
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                file_path, error = save_uploaded_file(file, 'permohonan')
                if error:
                    return error_response(f"Failed to save file: {error}", status_code=400)
                permohonan_data['file_name'] = file.filename
        
        # Create permohonan
        permohonan, error = permohonan_service.create_permohonan(
            current_user.id, permohonan_data, file_path
        )
        
        if error:
            return error_response(error, status_code=400)
        
        permohonan_data = permohonan_schema.dump(permohonan)
        return success_response("Permohonan created successfully", permohonan_data, 201)
        
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)
    except Exception as e:
        return error_response("Failed to create permohonan", str(e), 500)


@permohonan_bp.route('/<string:permohonan_id>/reject', methods=['POST'])
@role_required('dosen')
def reject_permohonan(permohonan_id):
    """Reject permohonan (dosen only)"""
    try:
        current_user = get_current_user_by_role_required()
        data = request.json or {}
        komentar_penolakan = data.get('komentar_penolakan')
        print('komentar_penolakan',komentar_penolakan)
        if not komentar_penolakan:
            return error_response("Rejection comment is required", status_code=400)
        
        permohonan, error = permohonan_service.reject_permohonan(
            permohonan_id, current_user.id, komentar_penolakan
        )
        
        if error:
            return error_response(error, status_code=400)
        
        permohonan_data = permohonan_schema.dump(permohonan)
        return success_response("Permohonan rejected successfully", permohonan_data)
        
    except Exception as e:
        return error_response("Failed to reject permohonan", str(e), 500)


@permohonan_bp.route('/<string:permohonan_id>/sign', methods=['POST'])
@role_required('dosen')
def sign_permohonan(permohonan_id):
    """Sign approved permohonan (dosen only)"""
    try:
        current_user = get_current_user_by_role_required()
        # Check if dosen has uploaded signature
        if not current_user.ttd_path:
            print(current_user.ttd_path,'ttd_path')
            return error_response("Please upload your signature first", status_code=400)
        
        permohonan, error = permohonan_service.sign_permohonan(permohonan_id, current_user.id)
        if error:
            return error_response(error, status_code=400)
        
        permohonan_data = permohonan_schema.dump(permohonan)
        return success_response("Permohonan signed successfully", permohonan_data)
        
    except Exception as e:
        print("eror sign",e)
        return error_response("Failed to sign permohonan", str(e), 500)

    
@permohonan_bp.route('/dosen', methods=['GET'])
@role_required('dosen')
def get_permohonan_for_dosen():
    """Get permohonan list for dosen with optional status & jenis filter"""
    try:
        status = request.args.get('status', 'pending')  # default pending
        jenis_id = request.args.get('jenis_id', type=int)
        current_user = get_current_user_by_role_required()

        permohonan_list = permohonan_service.get_permohonan_dosen(
            current_user.id, status, jenis_id
        )
        permohonan_data = permohonan_list_schema.dump(permohonan_list)
        return success_response("Permohonan list retrieved", permohonan_data)

    except Exception as e:
        return error_response("Failed to get permohonan for dosen", str(e), 500)


@permohonan_bp.route('/batch-sign', methods=['POST'])
@role_required('dosen')
def batch_sign_permohonan():
    """Batch sign multiple permohonan (dosen only)"""
    try:
        current_user = get_current_user_by_role_required()
        # Check if dosen has uploaded signature
        if not current_user.ttd_path:
            return error_response("Please upload your signature first", status_code=400)
        
        data = request.json or {}
        permohonan_ids = data.get('permohonan_ids', [])
        
        if not permohonan_ids or not isinstance(permohonan_ids, list):
            return error_response("permohonan_ids must be a non-empty array", status_code=400)
        
        # Call batch sign service
        result, error = permohonan_service.batch_sign_permohonan(
            permohonan_ids, 
            current_user.id
        )
        
        if error:
            return error_response(error, status_code=400)
        
        # Format response
        return success_response(
            f"Batch signing completed: {len(result['success'])} success, {len(result['failed'])} failed",
            result,
            200
        )
        
    except Exception as e:
        print("❌ Batch sign error:", str(e))
        print(traceback.format_exc())
        return error_response("Failed to batch sign permohonan", str(e), 500)



#belom digunakan
# @permohonan_bp.route('/<int:permohonan_id>/approve', methods=['POST'])
# @role_required('dosen')
# def approve_permohonan(current_user, permohonan_id):
#     """Approve permohonan (dosen only)"""
#     try:
#         data = request.json or {}
#         # komentar = data.get('komentar')
        
#         permohonan, error = permohonan_service.approve_permohonan(
#             permohonan_id, current_user.id
#             # komentar
#         )
        
#         if error:
#             return error_response(error, status_code=400)
        
#         permohonan_data = permohonan_schema.dump(permohonan)
#         return success_response("Permohonan approved successfully", permohonan_data)
        
#     except Exception as e:
#         return error_response("Failed to approve permohonan", str(e), 500)


# @permohonan_bp.route('/dashboard/stats', methods=['GET'])
# @role_required('admin', 'dosen')
# def get_dashboard_stats(current_user):
#     """Get dashboard statistics"""
#     print("GET DASHBOARD STATS")
#     try:
#         stats = permohonan_service.get_dashboard_stats()
#         return success_response("Dashboard statistics retrieved", stats)
        
#     except Exception as e:
#         return error_response("Failed to get dashboard stats", str(e), 500)

# @permohonan_bp.route('/pending', methods=['GET'])
# @role_required('dosen')
# def get_pending_permohonan(current_user):
#     """Get pending permohonan for dosen"""
#     try:
#         # current_user = get_current_user_by_role_required()
#         pending_list = permohonan_service.permohonan_repo.get_pending_by_dosen(current_user.id)
#         permohonan_data = permohonan_list_schema.dump(pending_list)
#         return success_response("Pending permohonan retrieved", permohonan_data)
        
#     except Exception as e:
#         return error_response("Failed to get pending permohonan", str(e), 500)