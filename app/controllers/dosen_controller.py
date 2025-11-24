#app/controller/dosen_controller.py
from flask import Blueprint, jsonify, request
from app.services.dosen_service import DosenService
from app.services.history_service import HistoryService
from flask_jwt_extended import jwt_required,get_jwt_identity
from utils.response_utils import success_response, error_response
from utils.file_utils import save_uploaded_file
from utils.jwt_utils import role_required, get_current_user,jwt_required
from PIL import Image

dosen_bp = Blueprint("dosen", __name__)
dosen_service = DosenService()
history_service = HistoryService()


def check_role_dosen():
    current_user = get_current_user()
    role = getattr(current_user, "role", None)

    if role != "dosen":
        return False, None, role
    return True, current_user, role

@dosen_bp.route("/", methods=["GET"])
def get_all_dosen():
    result = dosen_service.get_all_dosen()
    return jsonify(result), 200




@dosen_bp.route('/upload-signature', methods=['POST'])
@jwt_required()
def upload_signature():
    """Upload dosen signature"""
    try:
        # Ambil user ID dari JWT
        user_id = get_jwt_identity()

        if 'signature' not in request.files:
            return error_response("No signature file provided", status_code=400)
        
        file = request.files['signature']
        if file.filename == '':
            return error_response("No file selected", status_code=400)
        
        # Save file
        from utils.file_utils import save_signature_direct
        file_path, error = save_signature_direct(file)
        if error:
            return error_response(f"Failed to save signature: {error}", status_code=400)
        
        # Update dosen record
        dosen, error = dosen_service.upload_signature(user_id, file_path)
        if error:
            return error_response(error, status_code=500)
        
        from schemas.dosen_schema import DosenSchema
        dosen_schema = DosenSchema()
        dosen_data = dosen_schema.dump(dosen)
        return success_response("Signature uploaded successfully", dosen_data)
        
    except Exception as e:
        return error_response("Failed to upload signature", str(e), 500)
    

@dosen_bp.route("/stats", methods=['GET'])
@jwt_required()
def statistic_dosen():
    """
    Get jumlah permohonan mahasiswa berdasarkan status
    Contoh response:
    {
        "pending": 3,
        "ditolak": 1,
        "ditandatangani": 5
    }
    """
    try:
        is_dosen,current_user,role= check_role_dosen()
        if not is_dosen:
            return error_response("error you are not dosen",status_code=401)
        
        counts = history_service.get_all_counts_off_permohonan()
        
        if counts is None:
            return error_response("No History found",status_code=403)
        
        return success_response("History counts retrieved", counts)
        
    except Exception as e:
        return error_response("Failed to get counts", str(e), 500)


@dosen_bp.route("/recent-history", methods=['GET'])
@jwt_required()
def recent_history_dosen():

    try:

        is_dosen,current_user,role= check_role_dosen()
        if not is_dosen:
            return error_response("error you are not dosen",status_code=401)
        
        id_dosen = current_user.id
        
        recenHistory = history_service.get_all_permohonan_by_dosen(id_dosen)
        
        if recenHistory is None:
            return error_response("No History found",status_code=403)
        
        return success_response("History recenHistory retrieved", recenHistory)
        
    except Exception as e:
        return error_response("Failed to get history", str(e), 500)
