from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.services.history_service import HistoryService
from schemas.permohonan_schema import PermohonanSchema
from utils.response_utils import success_response, error_response
from utils.jwt_utils import role_required, get_current_user

# Blueprint
history_bp = Blueprint("history", __name__)

# Service dan schema
service_history = HistoryService()
schema_history = PermohonanSchema(many=True)


# @history_bp.route("/<string:status>", methods=["GET"])
# @jwt_required()
# @role_required('mahasiswa')
# def get_history_status(status):
#     """
#     Get data permohonan mahasiswa berdasarkan status
#     Contoh: /api/history/ditandatangani, /api/history/pending
#     """
#     try:
#         current_user = get_current_user()
#         user_id = current_user.id

#         history = service_history.get_history_by_status(user_id, status)
#         if not history:
#             return error_response("No history found", status_code=404)

#         return success_response("History retrieved", schema_history.dump(history))

#     except Exception as e:
#         print("Error get_history_status:", str(e))
#         return error_response("Failed to get history", str(e), 500)


@history_bp.route("/<string:status>", methods=["GET"])
@jwt_required()
def get_history_status(status):
    try:
        # ambil user dari JWT, jangan dari parameter
        current_user = get_current_user()
        user_id = current_user.id
        # print("Current User:", current_user.role, current_user.id)
        role = current_user.role
        
        history = service_history.get_history_by_status(user_id,role,status)
        # elif role == "dosen":
        # elif role == " admin":
        # print("role admin")
        # else:
            # pass
        if not history:
            return error_response("No history found", status_code=404)

        return success_response("History retrieved", schema_history.dump(history))

    except Exception as e:
        print("Error get_history_status:", str(e))
        return error_response("Failed to get history", str(e), 500)




@history_bp.route("/counts", methods=["GET"])
@jwt_required()
# @role_required('mahasiswa')
def get_counts_by_status():
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
        current_user = get_current_user()
        user_id = current_user.id
        role = current_user.role
        counts = service_history.get_counts_by_status(user_id,role)
        if counts is None:
            return error_response("No history found", status_code=404)

        return success_response("History counts retrieved", counts)

    except Exception as e:
        print("Error get_counts_by_status:", str(e))
        return error_response("Failed to get counts", str(e), 500)


@history_bp.route("/total", methods=["GET"])
@jwt_required()
def get_total_history():
    """
    Get total seluruh permohonan mahasiswa (semua status)
    Contoh response:
    {
        "total": 9
    }
    """
    try:
        current_user = get_current_user()
        user_id = current_user.id
        role = current_user.role
        total = service_history.get_total_permohonan(user_id,role)
        if total is None:
            return error_response("No history found", status_code=404)

        return success_response("Total history retrieved", {"total": total})

    except Exception as e:
        print("Error get_total_history:", str(e))
        return error_response("Failed to get total", str(e), 500)
    
@history_bp.route("/all", methods=["GET"])
@jwt_required()
# @role_required('mahasiswa')
def get_all_history():
    current_user = get_current_user()
    user_id = current_user.id
    role = current_user.role
    all_history = service_history.get_all_history(user_id,role)
    return success_response("All history retrieved", schema_history.dump(all_history))

