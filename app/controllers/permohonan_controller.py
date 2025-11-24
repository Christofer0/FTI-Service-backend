# controllers/permohonan_controller.py
from flask import Blueprint, request
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

@permohonan_bp.route('/', methods=['POST'])
@role_required('mahasiswa')
def create_permohonan(current_user):
    """Create new permohonan (mahasiswa only)"""
    try:
        # Get form data
        form_data = request.form.to_dict()
        # 🟢 DEBUG: log data yang masuk
        # print("📥 FORM DATA RAW:", request.form.to_dict())
        # print("📂 FILES RAW:", request.files.to_dict())
        # print("📄 HEADERS:", dict(request.headers))

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
        # print("❌ ERROR:", str(e))
        # print(traceback.format_exc())  # biar stacktrace kelihatan
        return error_response("Failed to create permohonan", str(e), 500)

@permohonan_bp.route('/', methods=['GET'])
@jwt_required()
def get_permohonan_list(current_user):
    """Get permohonan list based on user role"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status')
        
        # Get permohonan based on user role
        if current_user.role == 'mahasiswa':
            permohonan_list = permohonan_service.permohonan_repo.get_by_mahasiswa(
                current_user.id, status
            )
        elif current_user.role == 'dosen':
            permohonan_list = permohonan_service.permohonan_repo.get_by_dosen(
                current_user.id, status
            )
        elif current_user.role == 'admin':
            if status:
                permohonan_list = permohonan_service.permohonan_repo.get_by_status(status)
            else:
                permohonan_list = permohonan_service.permohonan_repo.get_all()
        else:
            return error_response("Unauthorized", status_code=403)
        
        # Simple pagination (for demo purposes)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_list = permohonan_list[start:end]
        
        # Create pagination object
        class PaginationObject:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_next = page < self.pages
                self.has_prev = page > 1
        
        pagination = PaginationObject(paginated_list, page, per_page, len(permohonan_list))
        
        permohonan_data = permohonan_list_schema.dump(paginated_list)
        return paginated_response(permohonan_data, pagination, "Permohonan list retrieved")
        
    except Exception as e:
        return error_response("Failed to get permohonan list", str(e), 500)

@permohonan_bp.route('/<int:permohonan_id>', methods=['GET'])
@jwt_required()
def get_permohonan_detail(current_user, permohonan_id):
    """Get permohonan detail"""
    try:
        permohonan = permohonan_service.permohonan_repo.get_with_details(permohonan_id)
        
        if not permohonan:
            return error_response("Permohonan not found", status_code=404)
        
        # Check authorization
        if current_user.role == 'mahasiswa' and permohonan.id_mahasiswa != current_user.id:
            return error_response("Unauthorized", status_code=403)
        elif current_user.role == 'dosen' and permohonan.id_dosen != current_user.id:
            return error_response("Unauthorized", status_code=403)
        
        permohonan_data = permohonan_schema.dump(permohonan)
        return success_response("Permohonan detail retrieved", permohonan_data)
        
    except Exception as e:
        return error_response("Failed to get permohonan detail", str(e), 500)


@permohonan_bp.route('/<int:permohonan_id>/approve', methods=['POST'])
@role_required('dosen')
def approve_permohonan(current_user, permohonan_id):
    """Approve permohonan (dosen only)"""
    try:
        data = request.json or {}
        # komentar = data.get('komentar')
        
        permohonan, error = permohonan_service.approve_permohonan(
            permohonan_id, current_user.id
            # komentar
        )
        
        if error:
            return error_response(error, status_code=400)
        
        permohonan_data = permohonan_schema.dump(permohonan)
        return success_response("Permohonan approved successfully", permohonan_data)
        
    except Exception as e:
        return error_response("Failed to approve permohonan", str(e), 500)

@permohonan_bp.route('/<string:permohonan_id>/reject', methods=['POST'])
@role_required('dosen')
def reject_permohonan(current_user, permohonan_id):
    """Reject permohonan (dosen only)"""
    try:
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
def sign_permohonan(current_user, permohonan_id):
    """Sign approved permohonan (dosen only)"""
    try:
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

@permohonan_bp.route('/dashboard/stats', methods=['GET'])
@role_required('admin', 'dosen')
def get_dashboard_stats(current_user):
    """Get dashboard statistics"""
    try:
        stats = permohonan_service.get_dashboard_stats()
        return success_response("Dashboard statistics retrieved", stats)
        
    except Exception as e:
        return error_response("Failed to get dashboard stats", str(e), 500)

@permohonan_bp.route('/pending', methods=['GET'])
@role_required('dosen')
def get_pending_permohonan(current_user):
    """Get pending permohonan for dosen"""
    try:
        pending_list = permohonan_service.permohonan_repo.get_pending_by_dosen(current_user.id)
        permohonan_data = permohonan_list_schema.dump(pending_list)
        return success_response("Pending permohonan retrieved", permohonan_data)
        
    except Exception as e:
        return error_response("Failed to get pending permohonan", str(e), 500)
    

@permohonan_bp.route('/dosen', methods=['GET'])
@role_required('dosen')
def get_permohonan_for_dosen(current_user):
    """Get permohonan list for dosen with optional status & jenis filter"""
    try:
        status = request.args.get('status', 'pending')  # default pending
        jenis_id = request.args.get('jenis_id', type=int)

        permohonan_list = permohonan_service.get_permohonan_dosen(
            current_user.id, status, jenis_id
        )
        permohonan_data = permohonan_list_schema.dump(permohonan_list)
        return success_response("Permohonan list retrieved", permohonan_data)

    except Exception as e:
        return error_response("Failed to get permohonan for dosen", str(e), 500)

    
# controllers/permohonan_controller.py
@permohonan_bp.route('/batch-sign', methods=['POST'])
@role_required('dosen')
def batch_sign_permohonan(current_user):
    """Batch sign multiple permohonan (dosen only)"""
    try:
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