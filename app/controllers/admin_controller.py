from flask import Blueprint,request,g
from utils.jwt_utils import role_required, get_current_user,jwt_required
from utils.response_utils import success_response, error_response
from app.services.history_service import HistoryService
from app.services.user_service import UserService
from schemas.permohonan_schema import PermohonanSchema
from app.services.view_user_service import ViewRepositoryDosen, ViewRepositoryMahasiswa

admin_bp = Blueprint('admin', __name__)
service_history = HistoryService()
service_user = UserService()
permohonan_schema = PermohonanSchema()
view_mhs_service = ViewRepositoryMahasiswa()
view_dosen_service = ViewRepositoryDosen()

def get_current_user_and_role_by_role_req():
    current_user = g.current_user
    role = g.current_user.role if current_user else None
    return current_user,role


@admin_bp.route('/users', methods=['GET'])
@role_required('admin')
def get_all_users():
    """Get all users (admin only)"""
    try:        
        users, _ = service_user.get_all()  # unpack tuple
        print(type(users), "ini get_all users")

        # ubah ke list of dicts
        users_list = [user.to_dict() for user in users]

        return success_response("Users retrieved", users_list)
    except Exception as e:
        return error_response("Failed to get users", str(e), 500)


@admin_bp.route('/users/role/<role>', methods=['GET'])
@role_required('admin')
def get_users_by_role(role):
    """Get users by role (admin only)"""
    try:
        if role not in ["mahasiswa","dosen"]:
            return error_response("invalid response", status_code=400)   
        
        if role == "mahasiswa":
            users_list = view_mhs_service.get_all_mahasiswa()
        else:
            users_list = view_dosen_service.get_all_dosen()

        return success_response(f"Users with role {role} retrieved", users_list)
    except Exception as e:
        return error_response("Failed to get users by role", str(e), 500)
    

@admin_bp.route('/users/<user_id>/<action>', methods=['POST'])
@role_required('admin')
def toggle_user_status(user_id,action):
    """Toggle user active status (admin only)"""
    try:
        update_isActive = service_user.toggle_status(user_id,action)

        return success_response("User status updated",update_isActive)
    except Exception as e:
        return error_response("Failed to update user status", str(e), 500)
    
    
@admin_bp.route("/stats", methods=['GET'])
@role_required('admin')
def statistic_admin():
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
        current_user, role = get_current_user_and_role_by_role_req()
        
        counts = service_history.get_counts_by_status(current_user,role)
        
        if counts is None:
            return error_response("No History found",status_code=403)
        
        return success_response("History counts retrieved", counts)
        
    except Exception as e:
        return error_response("Failed to get counts", str(e), 500)
    

@admin_bp.route('/permohonan/<string:status>', methods=['GET'])
@role_required('admin')
def get_all_permohonan(status):
    """
    Ambil semua data permohonan — seperti SELECT * FROM permohonan
    """
    try:
        current_user , role = get_current_user_and_role_by_role_req()
        print(current_user,role)
        # Ambil semua data dari repo
        role = current_user.role
        permohonan_list = service_history.get_history_by_status(current_user,role, status)

        if not permohonan_list:
            return error_response("No data found", status_code=404)

        # Serialize pakai schema Marshmallow
        data = permohonan_schema.dump(permohonan_list, many=True)

        return success_response("All permohonan retrieved", data)

    except Exception as e:
        print("Error get_all_permohonan:", str(e))
        return error_response("Failed to retrieve data", str(e), 500)
    
