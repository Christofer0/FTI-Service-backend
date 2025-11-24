# controllers/user_controller.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required,get_jwt_identity
from marshmallow import ValidationError

from app.services.user_service import UserService
from app.services.notification_service import NotificationService
from schemas.user_schema import UserSchema, UpdateUserSchema
from schemas.notification_schema import NotificationSchema
from utils.jwt_utils import role_required
from utils.response_utils import success_response, error_response
from utils.file_utils import save_uploaded_file

user_bp = Blueprint('users', __name__)
user_service = UserService()
notification_service = NotificationService()

# Schema instances
user_schema = UserSchema()
update_user_schema = UpdateUserSchema()
notification_schema = NotificationSchema(many=True)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile(current_user):
    try:
        profile_data, error = user_service.get_user_profile(current_user.id)
        if error:
            return error_response(error, status_code=404)

        # serialize user dasar
        user_data = user_schema.dump(profile_data['user'])

        # pastikan selalu ada field mahasiswa & dosen
        user_data['mahasiswa'] = None
        user_data['dosen'] = None

        if profile_data['role_data']:
            if current_user.role == 'mahasiswa':
                from schemas.mahasiswa_schema import MahasiswaSchema
                mahasiswa_schema = MahasiswaSchema()
                user_data['mahasiswa'] = mahasiswa_schema.dump(profile_data['role_data'])
            elif current_user.role == 'dosen':
                from schemas.dosen_schema import DosenSchema
                dosen_schema = DosenSchema()
                user_data['dosen'] = dosen_schema.dump(profile_data['role_data'])

        return success_response("Profile retrieved", user_data)
    except Exception as e:
        return error_response("Failed to get profile", str(e), 500)


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        # Ambil user id dari token
        current_user_id = get_jwt_identity()

        # Validate request data
        update_data = update_user_schema.load(request.json)
        
        # Update profile
        user, error = user_service.update_user_profile(current_user_id, update_data)
        
        if error:
            return error_response(error, status_code=400)
        
        user_data = user_schema.dump(user)
        
        return success_response("Profile updated successfully", user_data)
        
    except ValidationError as e:
        return error_response("Validation error", e.messages, 400)
    except Exception as e:
        return error_response("Failed to update profile", str(e), 500)

@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not old_password or not new_password:
            return error_response("Old password and new password are required", status_code=400)

        if len(new_password) < 6:
            return error_response("New password must be at least 6 characters", status_code=400)

        # Ambil user_id dari JWT
        user_id = get_jwt_identity()

        success, message = user_service.change_password(user_id, old_password, new_password)

        if not success:
            return error_response(message, status_code=400)

        return success_response(message)

    except Exception as e:
        return error_response("Failed to change password", str(e), 500)

@user_bp.route('/upload-signature', methods=['POST'])
@jwt_required()
def upload_signature(current_user):
    """Upload user signature"""
    try:
        if 'signature' not in request.files:
            return error_response("No signature file provided", status_code=400)
        
        file = request.files['signature']
        if file.filename == '':
            return error_response("No file selected", status_code=400)
        
        # Save file
        file_path, error = save_uploaded_file(file, 'signatures')
        if error:
            return error_response(f"Failed to save signature: {error}", status_code=400)
        
        # Update user record
        user, error = user_service.upload_signature(current_user.id, file_path)
        if error:
            return error_response(error, status_code=500)
        
        user_data = user_schema.dump(user)
        return success_response("Signature uploaded successfully", user_data)
        
    except Exception as e:
        return error_response("Failed to upload signature", str(e), 500)

@user_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications(current_user):
    """Get user notifications"""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        notifications = notification_service.get_user_notifications(current_user.id, unread_only)
        
        notifications_data = notification_schema.dump(notifications)
        return success_response("Notifications retrieved", notifications_data)
        
    except Exception as e:
        return error_response("Failed to get notifications", str(e), 500)

@user_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(current_user, notification_id):
    """Mark notification as read"""
    try:
        success = notification_service.mark_notification_read(notification_id, current_user.id)
        
        if success:
            return success_response("Notification marked as read")
        else:
            return error_response("Notification not found", status_code=404)
        
    except Exception as e:
        return error_response("Failed to mark notification as read", str(e), 500)

@user_bp.route('/notifications/read-all', methods=['POST'])
@jwt_required()
def mark_all_notifications_read(current_user):
    """Mark all notifications as read"""
    try:
        count = notification_service.mark_all_notifications_read(current_user.id)
        return success_response(f"Marked {count} notifications as read", {'updated_count': count})
        
    except Exception as e:
        return error_response("Failed to mark notifications as read", str(e), 500)
