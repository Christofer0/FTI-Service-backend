# from flask import send_from_directory, current_app, Blueprint, abort
# import os

# file_bp = Blueprint('files', __name__)

# # file_controller.py
# @file_bp.route('/uploads/<path:filename>', methods=['GET'])
# def serve_uploaded_file(filename):
#     upload_folder = current_app.config['UPLOAD_FOLDER']  # ini = storage/uploads
#     full_path = os.path.join(upload_folder, filename)
#     if not os.path.exists(full_path):
#         abort(404)
#     return send_from_directory(upload_folder, filename, as_attachment=False)

# controllers/file_controller.py
from flask import send_from_directory, current_app, Blueprint, abort
import os

file_bp = Blueprint('files', __name__)

# Route yang sudah ada
@file_bp.route('/uploads/<path:filename>', methods=['GET'])
def serve_uploaded_file(filename):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    full_path = os.path.join(upload_folder, filename)
    if not os.path.exists(full_path):
        abort(404)
    return send_from_directory(upload_folder, filename, as_attachment=False)

# TAMBAHKAN ROUTE BARU INI
@file_bp.route('/signed/<path:filename>', methods=['GET'])
def serve_signed_file(filename):
    """Serve signed PDF files"""
    try:
        signed_folder = current_app.config['UPLOAD_SIGNED']
        full_path = os.path.join(signed_folder, filename)
        
        if not os.path.exists(full_path):
            abort(404)
        
        directory = os.path.dirname(full_path)
        filename_only = os.path.basename(full_path)
        
        return send_from_directory(directory, filename_only, as_attachment=False)
        
    except Exception as e:
        print(f"Error serving signed file: {e}")
        abort(404)