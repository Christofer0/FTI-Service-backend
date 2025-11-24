# # utils/qr_utils.py
# import qrcode
# import hashlib
# import hmac
# import json
# import os
# from datetime import datetime
# from flask import current_app
# from PIL import Image

# def generate_verification_signature(data, secret_key):
#     """Generate HMAC signature for QR code security"""
#     message = json.dumps(data, sort_keys=True)
#     signature = hmac.new(
#         secret_key.encode(),
#         message.encode(),
#         hashlib.sha256
#     ).hexdigest()
#     return signature

# def generate_qr_code(data, permohonan_id):
#     """Generate QR code with verification URL and signature"""
#     try:
#         # Get base URL from config (use localhost:5173 for frontend)
#         frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
        
#         # Create verification URL
#         verify_url = f"{frontend_url}/verify-document/{permohonan_id}"
        
#         # Create signature for security
#         secret_key = current_app.config['SECRET_KEY']
#         signature_data = {
#             'permohonan_id': str(permohonan_id),
#             'signed_at': data.get('signed_at'),
#             'signed_by': data.get('signed_by')
#         }
#         signature = generate_verification_signature(signature_data, secret_key)
        
#         # QR Code will only contain the URL
#         qr_content = verify_url
        
#         # Store full data for backend verification
#         qr_data = {
#             'permohonan_id': str(permohonan_id),
#             'verify_url': verify_url,
#             'signature': signature,
#             'timestamp': datetime.utcnow().isoformat(),
#             'data': data
#         }
        
#         # Create QR code
#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
#             box_size=10,
#             border=4,
#         )
#         qr.add_data(qr_content)
#         qr.make(fit=True)
        
#         # Create QR code image
#         img = qr.make_image(fill_color="black", back_color="white")
        
#         # Save QR code
#         qr_folder = current_app.config['QR_CODE_FOLDER']
#         os.makedirs(qr_folder, exist_ok=True)
        
#         filename = f"qr_{permohonan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
#         file_path = os.path.join(qr_folder, filename)
        
#         img.save(file_path)
        
#         return filename, json.dumps(qr_data), None
        
#     except Exception as e:
#         return None, None, str(e)

# def verify_qr_signature(permohonan_id, signed_at, signed_by, provided_signature, secret_key):
#     """Verify QR code signature"""
#     try:
#         signature_data = {
#             'permohonan_id': str(permohonan_id),
#             'signed_at': signed_at,
#             'signed_by': signed_by
#         }
#         calculated_signature = generate_verification_signature(signature_data, secret_key)
#         return hmac.compare_digest(calculated_signature, provided_signature)
#     except Exception as e:
#         print(f"Signature verification error: {e}")
#         return False

# utils/qr_utils.py
import qrcode
import hashlib
import hmac
import json
import os
from datetime import datetime
from flask import current_app
from PIL import Image

def generate_verification_signature(data, secret_key):
    """Generate HMAC signature for QR code security"""
    message = json.dumps(data, sort_keys=True)
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def generate_qr_code(data, permohonan_id):
    """Generate QR code with verification URL and signature"""
    try:
        # Get base URL from config
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
        
        # Create verification URL
        verify_url = f"{frontend_url}/verify-document/{permohonan_id}"
        
        # Create signature for security
        secret_key = current_app.config['SECRET_KEY']
        signature_data = {
            'permohonan_id': str(permohonan_id),
            'signed_at': data.get('signed_at'),
            'signed_by': data.get('signed_by')
        }
        signature = generate_verification_signature(signature_data, secret_key)
        
        # QR Code will only contain the URL
        qr_content = verify_url
        
        # Store full data for backend verification
        qr_data = {
            'permohonan_id': str(permohonan_id),
            'verify_url': verify_url,
            'signature': signature,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_folder = current_app.config['QR_CODE_FOLDER']
        os.makedirs(qr_folder, exist_ok=True)
        
        filename = f"qr_{permohonan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path = os.path.join(qr_folder, filename)
        
        img.save(file_path)
        
        return filename, json.dumps(qr_data), None
        
    except Exception as e:
        return None, None, str(e)

def verify_qr_signature(permohonan_id, signed_at, signed_by, provided_signature, secret_key):
    """Verify QR code signature"""
    try:
        signature_data = {
            'permohonan_id': str(permohonan_id),
            'signed_at': signed_at,
            'signed_by': signed_by
        }
        calculated_signature = generate_verification_signature(signature_data, secret_key)
        return hmac.compare_digest(calculated_signature, provided_signature)
    except Exception as e:
        print(f"Signature verification error: {e}")
        return False
