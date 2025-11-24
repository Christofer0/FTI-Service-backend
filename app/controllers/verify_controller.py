# controllers/verify_controller.py
from flask import Blueprint, jsonify
from app.repositories.permohonan_repository import PermohonanRepository
from utils.response_utils import success_response, error_response
import json

verify_bp = Blueprint('verify', __name__)
permohonan_repo = PermohonanRepository()

@verify_bp.route('/<string:permohonan_id>', methods=['GET'])
def verify_document(permohonan_id):
    """
    Public endpoint to verify signed document via QR code
    No authentication required
    """
    try:
        # Get permohonan
        permohonan = permohonan_repo.get_by_id(permohonan_id)
        
        # Check if permohonan exists
        if not permohonan:
            return error_response(
                "Dokumen tidak ditemukan",
                "Permohonan dengan ID tersebut tidak ada dalam sistem",
                404
            )
        
        # Check if document is signed (valid)
        if permohonan.status_permohonan != 'ditandatangani':
            return error_response(
                "Dokumen tidak valid",
                f"Status dokumen: {permohonan.status_permohonan}. Dokumen belum ditandatangani atau sudah tidak berlaku.",
                400
            )
        
        # Verify QR signature if exists
        if permohonan.qr_code_data:
            try:
                qr_data = json.loads(permohonan.qr_code_data)
                signature = qr_data.get('signature')
                
                if signature:
                    from flask import current_app
                    from utils.qr_utils import verify_qr_signature
                    
                    original_data = qr_data.get('data', {})
                    is_valid = verify_qr_signature(
                        permohonan.id,
                        original_data.get('signed_at'),
                        original_data.get('signed_by'),
                        signature,
                        current_app.config['SECRET_KEY']
                    )
                    
                    if not is_valid:
                        return error_response(
                            "Dokumen tidak valid",
                            "Signature QR Code tidak valid. Dokumen mungkin telah dimodifikasi.",
                            400
                        )
            except Exception as e:
                print(f"QR verification error: {e}")
                # Continue without failing if QR verification has issues
        
        # Prepare response data
        response_data = {
            'status': 'valid',
            'permohonan_id': permohonan.id,
            'jenis_permohonan': {
                'id': permohonan.jenis_permohonan.id,
                'nama': permohonan.jenis_permohonan.nama_jenis_permohonan
            } if permohonan.jenis_permohonan else None,
            'judul': permohonan.judul,
            'deskripsi': permohonan.deskripsi,
            'mahasiswa': {
                'nama': permohonan.mahasiswa.user.nama if permohonan.mahasiswa and permohonan.mahasiswa.user else 'N/A',
                'nomor_induk': permohonan.mahasiswa.user.nomor_induk if permohonan.mahasiswa and permohonan.mahasiswa.user else 'N/A',  # FIXED: dari users table
                'program_studi': permohonan.mahasiswa.program_studi.nama_prodi if permohonan.mahasiswa and permohonan.mahasiswa.program_studi else 'N/A',
                'fakultas': permohonan.mahasiswa.program_studi.fakultas.nama_fakultas if permohonan.mahasiswa and permohonan.mahasiswa.program_studi and permohonan.mahasiswa.program_studi.fakultas else 'N/A'
            },
            'dosen': {
                'nama': permohonan.dosen.user.nama if permohonan.dosen and permohonan.dosen.user else 'N/A'
            },
            'signed_at': permohonan.signed_at.isoformat() if permohonan.signed_at else None,
            'created_at': permohonan.created_at.isoformat() if permohonan.created_at else None
        }
        
        return success_response(
            "Dokumen valid dan telah ditandatangani",
            response_data
        )
        
    except Exception as e:
        print(f"Verify error: {e}")
        return error_response(
            "Terjadi kesalahan",
            "Gagal memverifikasi dokumen. Silakan coba lagi.",
            500
        )