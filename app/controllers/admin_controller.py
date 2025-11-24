
# controllers/admin_controller.py (Additional controller for admin functions)
from flask import Blueprint,request
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

def check_role_admin():
    current_user = get_current_user()
    role = getattr(current_user, "role", None)

    if role != "admin":
        return False, None, role
    return True, current_user, role


# @admin_bp.route('/users', methods=['GET'])
# @jwt_required()
# def get_all_users():
#     """Get all users (admin only)"""
#     try:
#         is_admin,current_user,role = check_role_admin()
#         if not is_admin:
#             return error_response("You are not Admin",status_code=401)
        
#         get_all_users = service_user.get_all()
#         print(type(get_all_users),"ini geta ll users")

#         return success_response("Users retrieved", dict(get_all_users))
#     except Exception as e:
#         return error_response("Failed to get users", str(e), 500)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all users (admin only)"""
    try:
        is_admin, current_user, role = check_role_admin()
        if not is_admin:
            return error_response("You are not Admin", status_code=401)
        
        users, _ = service_user.get_all()  # unpack tuple
        print(type(users), "ini get_all users")

        # ubah ke list of dicts
        users_list = [user.to_dict() for user in users]

        return success_response("Users retrieved", users_list)
    except Exception as e:
        return error_response("Failed to get users", str(e), 500)


@admin_bp.route('/users/role/<role>', methods=['GET'])
@jwt_required()
def get_users_by_role(role):
    """Get users by role (admin only)"""
    try:
        is_admin, current_user, current_role = check_role_admin()
        if not is_admin:
            return error_response("You are not Admin", status_code=401)
        
        
        if role == "mahasiswa":
            users = view_mhs_service.get_all()
        elif role == "dosen":
            users = view_dosen_service.get_all()

        # ubah ke list of dicts
        users_list = [user.to_dict() for user in users]

        return success_response(f"Users with role {role} retrieved", users_list)
    except Exception as e:
        return error_response("Failed to get users by role", str(e), 500)
    
@admin_bp.route('/users/<user_id>/<action>', methods=['POST'])
@jwt_required()
def toggle_user_status(user_id,action):
    print(action, "ini action")
    """Toggle user active status (admin only)"""
    try:
        is_admin, current_user, role = check_role_admin()
        if not is_admin:
            return error_response("You are not Admin", status_code=401)
        
        update_isActive = service_user.toggle_status(user_id,action)

        return success_response("User status updated",update_isActive)
    except Exception as e:
        return error_response("Failed to update user status", str(e), 500)
    
@admin_bp.route("/stats", methods=['GET'])
@jwt_required()
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
        is_admin,current_user,role = check_role_admin()
        if not is_admin:
            return error_response("error you are not admin",status_code=401)
        
        counts = service_history.get_counts_by_status(current_user,role)
        
        if counts is None:
            return error_response("No History found",status_code=403)
        
        return success_response("History counts retrieved", counts)
        
    except Exception as e:
        return error_response("Failed to get counts", str(e), 500)
    
# @history_bp.route("/counts", methods=["GET"])
# @jwt_required()
# # @role_required('mahasiswa')
# def get_counts_by_status():
#     """
#     Get jumlah permohonan mahasiswa berdasarkan status
#     Contoh response:
#     {
#         "pending": 3,
#         "ditolak": 1,
#         "ditandatangani": 5
#     }
#     """
#     try:
#         current_user = get_current_user()
#         user_id = current_user.id
#         role = current_user.role
#         counts = service_history.get_counts_by_status(user_id,role)
#         if counts is None:
#             return error_response("No history found", status_code=404)

#         return success_response("History counts retrieved", counts)

#     except Exception as e:
#         print("Error get_counts_by_status:", str(e))
#         return error_response("Failed to get counts", str(e), 500)
    
# @admin_bp.route('/permohonan-list', methods=['GET'])
# # @role_required('admin')
# @jwt_required()
# def get_all_permohonan():
#     """Toogle permohonan pending"""
#     is_admin, user, role = check_role_admin()
#     if not is_admin:
#         return error_response("You are not Admin", status_code=403)
#     try:
#         list_permohonan = service_history.get_all_history(user,role)

#         if not list_permohonan:
#             return error_response("No history found", status_code=404)
#         permohonan_list = permohonan_schema.dump(list_permohonan)
#         print(permohonan_list)
#         return success_response("History counts retrieved",permohonan_list)
        
#     except Exception as e:
#         print("Error Get ALL history FOR ADMIN: ", str(e))
#         return error_response("Failed to get counts", str(e), 500)



# permohonan_data = permohonan_schema.dump(permohonan)
# return success_response("Permohonan detail retrieved", permohonan_data)
    
# @admin_bp.route('/permohonan/<string:status>', methods=['GET'])
# @jwt_required()
# def get_permohonan_admin(status):
#     """
#     Ambil permohonan (semua atau berdasarkan status) — khusus admin
#     Contoh:
#     - /api/admin/permohonan → semua
#     - /api/admin/permohonan?status=pending → hanya pending
#     """
#     try:
#         current_user = get_current_user()
#         if current_user.role != "admin":
#             return error_response("You are not Admin", status_code=403)

#         # Ambil parameter status dari query string (?status=xxx)
#         print("DEBIG STATUS: ",status)
#         if status:
#             # Ambil berdasarkan status
#             permohonan_list = service_history.get_history_by_status(
#                 user_id=current_user.id,
#                 role=current_user.role,
#                 status=status
#             )
#         else:
#             return error_response("GAADA",status_code=403)
#             # Ambil semua permohonan
#             # permohonan_list = service_history.get_all_history(
#             #     user_id=current_user.id,
#             #     role=current_user.role
#             # )

#         if not permohonan_list:
#             return error_response("No permohonan found", status_code=404)

#         return success_response(
#             "Permohonan retrieved successfully",
#             permohonan_schema.dump(permohonan_list)
#         )

#     except Exception as e:
#         print("Error get_permohonan_admin:", str(e))
#         return error_response("Failed to retrieve permohonan", str(e), 500)


@admin_bp.route('/permohonan/<string:status>', methods=['GET'])
@jwt_required()
def get_all_permohonan(status):
    """
    Ambil semua data permohonan — seperti SELECT * FROM permohonan
    """
    try:
        current_user = get_current_user()
        if current_user.role != "admin":
            return error_response("You are not Admin", status_code=403)


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
    

# @admin_bp.route('/users', methods=['GET'])
# @jwt_required()
# def get_all_user():
#     """Ambil semua user"""
#     try:
#         is_admin,current_user,role = check_role_admin()

