import os
from datetime import datetime
from .base_service import BaseService
from app.repositories.permohonan_repository import PermohonanRepository
from app.repositories.user_repository import UserRepository
from app.models.permohonan_model import Permohonan
from app.models.history_model import History
from utils.qr_utils import generate_qr_code
from utils.notification_utils import *
from extensions import db
from flask import current_app
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class PermohonanService(BaseService):
    """Service for permohonan operations"""
    
    def __init__(self):
        self.permohonan_repo = PermohonanRepository()
        self.user_repo = UserRepository()


    def create_permohonan(self, mahasiswa_id: str, permohonan_data: dict, file_path: str = None):
        """Create new permohonan"""
        try:
            permohonan = Permohonan(
                id_jenis_permohonan=permohonan_data['id_jenis_permohonan'],
                id_mahasiswa=mahasiswa_id,
                id_dosen=permohonan_data['id_dosen'],
                judul=permohonan_data['judul'],
                deskripsi=permohonan_data.get('deskripsi'),
                file_path=file_path,
                file_name=permohonan_data.get('file_name'),
                status_permohonan='pending'
            )
            
            db.session.add(permohonan)
            db.session.flush()
            
            # Create history record
            # self._create_history_record(permohonan, 'created')
            
            db.session.commit()
            
            # Send notification to dosen
            # notify_permohonan_created(permohonan)
            
            return permohonan, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)


    def get_permohonan_by_user(self, user_id: str, role: str):
        """Get permohonan by user based on role"""
        if role == 'mahasiswa':
            return self.permohonan_repo.get_by_mahasiswa(user_id)
        elif role == 'dosen':
            return self.permohonan_repo.get_by_dosen(user_id)
        elif role == 'admin':
            return self.permohonan_repo.get_all()
        else:
            return []


    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        return self.permohonan_repo.get_dashboard_stats()

    

    # DOSEN
    def get_permohonan_dosen(self, dosen_id: str, status: str = None, jenis_id: int = None):
        """Get permohonan untuk halaman dosen"""
        return self.permohonan_repo.get_by_dosen_with_filter(dosen_id, status, jenis_id)


    def reject_permohonan(self, permohonan_id: int, dosen_id: str, komentar_penolakan: str):
        """Reject permohonan"""
        try:
            permohonan = self.permohonan_repo.get_by_id(permohonan_id)
            
            if not permohonan:
                return None, "Permohonan not found"
            
            if permohonan.id_dosen != dosen_id:
                return None, "Unauthorized to reject this permohonan"
            
            if permohonan.status_permohonan != 'pending':
                return None, "Permohonan cannot be rejected"
            
            # Update status
            permohonan.status_permohonan = 'ditolak'
            permohonan.rejected_at = datetime.utcnow()
            permohonan.komentar_penolakan = komentar_penolakan
            
            # Create history record
            # self._create_history_record(permohonan, 'rejected', komentar_penolakan)
            
            db.session.commit()
            
            #remove file
            from utils.file_utils import delete_file
            file_permohonan_path = permohonan.file_path

            if file_permohonan_path:
                delete_file(file_permohonan_path)

            # Send notification to mahasiswa
            # notify_permohonan_rejected(permohonan)

            # Ambil user mahasiswa dari permohonan
            from app.models.user_model import User
            mahasiswa_user = db.session.query(User).filter_by(id=permohonan.id_mahasiswa).first()

            # Ambil user dosen dari user_id
            dosen_user = db.session.query(User).filter_by(id=dosen_id).first()

            from utils.email_utils import send_permohonan_email

            status, err = send_permohonan_email(
                mahasiswa_user.email,
                mahasiswa_user.nama,
                dosen_user.nama,
                "ditolak",
                komentar_penolakan
            )
                       
            return permohonan, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)


    def sign_permohonan(self, permohonan_id: str, dosen_id: str):
        """Sign permohonan (can sign pending or approved)"""
        try:
            permohonan = self.permohonan_repo.get_by_id(permohonan_id)
            if not permohonan:
                return None, "Permohonan not found"
            
            if permohonan.id_dosen != dosen_id:
                return None, "Unauthorized to sign this permohonan"
            
            if permohonan.status_permohonan not in ['pending', 'disetujui']:
                return None, "Permohonan cannot be signed"
            
            # Check if file exists
            if not permohonan.file_path:
                return None, "No file attached to this permohonan"
            
            
            # Get mahasiswa data
            from app.models.mahasiswa_model import Mahasiswa
            mahasiswa = db.session.query(Mahasiswa).filter_by(user_id=permohonan.id_mahasiswa).first()
            if not mahasiswa:
                return None, "Mahasiswa data not found"
            
            # Get dosen data
            from app.models.dosen_model import Dosen
            dosen = db.session.query(Dosen).filter_by(user_id=dosen_id).first()
            if not dosen or not dosen.ttd_path:
                return None, "Dosen signature not found"
            
            # Generate QR code with enhanced data
            qr_data = {
                'permohonan_id': str(permohonan.id),
                'signed_by': dosen_id,
                'signed_at': datetime.utcnow().isoformat(),
                'request_by': {
                    'nama': mahasiswa.user.nama if mahasiswa.user else 'Unknown',
                    'nomor_induk': mahasiswa.user.nomor_induk
                }
            }
            
            qr_filename, qr_data_string, qr_error = generate_qr_code(qr_data, permohonan.id)
            if qr_error:
                return None, f"Failed to generate QR code: {qr_error}"
            
            # ADD SIGNATURE TO PDF
            signed_pdf_error = self._add_signature_to_permohonan_pdf_single(
                permohonan, 
                dosen.ttd_path, 
                qr_filename,
                dosen_id
            )
            if signed_pdf_error:
                return None, signed_pdf_error
            
            # Update status
            permohonan.status_permohonan = 'ditandatangani'
            permohonan.signed_at = datetime.utcnow()
            permohonan.qr_code_path = qr_filename
            permohonan.qr_code_data = qr_data_string
            
            # Create history
            # self._create_history_record(permohonan, 'signed')
            
            db.session.commit()
            
            #remove file
            from utils.file_utils import delete_file
            file_permohonan_path = permohonan.file_path

            if file_permohonan_path:
                delete_file(file_permohonan_path)


            # Send notification
            # notify_permohonan_signed(permohonan)

            from app.models.user_model import User
            from utils.email_utils import send_permohonan_email

            mahasiswa_user = db.session.query(User).filter_by(id=permohonan.id_mahasiswa).first()
            dosen_user = db.session.query(User).filter_by(id=dosen_id).first()

            status, err = send_permohonan_email(
                mahasiswa_user.email,
                mahasiswa_user.nama,
                dosen_user.nama,
                "ditandatangani",
                None
            )
            return permohonan, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
        

    def batch_sign_permohonan(self, permohonan_ids: list, dosen_id: str):
        """Batch sign multiple permohonan dengan parallel processing untuk PDF dan email"""
        results = {
            'success': [],
            'failed': [],
            'total': len(permohonan_ids)
        }
        
        try:
            # ✅ GET FLASK APP CONTEXT (CRITICAL!)
            app = current_app._get_current_object()
            
            # Get dosen data once (optimization)
            from app.models.dosen_model import Dosen
            dosen = db.session.query(Dosen).filter_by(user_id=dosen_id).first()
            if not dosen or not dosen.ttd_path:
                return None, "Dosen signature not found"
            
            # Fetch all permohonan at once with eager loading
            from app.models.mahasiswa_model import Mahasiswa
            from app.models.user_model import User
            from sqlalchemy.orm import joinedload
            
            # ✅ EAGER LOAD semua relasi yang dibutuhkan
            permohonan_list = db.session.query(Permohonan)\
                .options(
                    joinedload(Permohonan.mahasiswa).joinedload(Mahasiswa.user),
                    joinedload(Permohonan.jenis_permohonan)
                )\
                .filter(Permohonan.id.in_(permohonan_ids))\
                .all()
            
            # Validate all permohonan first
            validated_permohonan = []
            for permohonan in permohonan_list:
                # Validasi
                if permohonan.id_dosen != dosen_id:
                    results['failed'].append({
                        'id': permohonan.id,
                        'reason': 'Unauthorized - not your permohonan'
                    })
                    continue
                
                if permohonan.status_permohonan not in ['pending', 'disetujui']:
                    results['failed'].append({
                        'id': permohonan.id,
                        'reason': f'Cannot sign (status: {permohonan.status_permohonan})'
                    })
                    continue
                
                if not permohonan.file_path:
                    results['failed'].append({
                        'id': permohonan.id,
                        'reason': 'No file attached'
                    })
                    continue
                
                validated_permohonan.append(permohonan)
            
            # Check for missing IDs
            found_ids = {p.id for p in permohonan_list}
            for pid in permohonan_ids:
                if pid not in found_ids:
                    results['failed'].append({
                        'id': pid,
                        'reason': 'Permohonan not found'
                    })
            
            if not validated_permohonan:
                return results, None
            
            # ✅ PRE-LOAD semua data yang dibutuhkan untuk parallel processing
            pdf_processing_tasks = []
            for permohonan in validated_permohonan:
                # Extract data di main thread (dalam app context)
                task_data = {
                    'permohonan_id': permohonan.id,
                    'permohonan_judul': permohonan.judul,
                    'file_path': permohonan.file_path,
                    'mahasiswa_nama': permohonan.mahasiswa.user.nama if permohonan.mahasiswa and permohonan.mahasiswa.user else 'Unknown',
                    'mahasiswa_nomor_induk': permohonan.mahasiswa.user.nomor_induk if permohonan.mahasiswa and permohonan.mahasiswa.user else None,
                    'mahasiswa_email': permohonan.mahasiswa.user.email if permohonan.mahasiswa and permohonan.mahasiswa.user else None,
                    'jenis_nama': permohonan.jenis_permohonan.nama_jenis_permohonan if permohonan.jenis_permohonan else '-'
                }
                pdf_processing_tasks.append(task_data)
            
            # ===== PARALLEL PROCESSING: QR Generation + PDF Signing =====
            
            
            pdf_processing_data = []
            emails_to_send = {}
            
            # Use ThreadPoolExecutor for parallel PDF processing
            max_workers = min(10, len(pdf_processing_tasks))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all PDF processing tasks
                future_to_task = {
                    executor.submit(
                        self._process_single_pdf_parallel_with_context,
                        app,  # ✅ Pass Flask app
                        task_data,
                        dosen.ttd_path,
                        dosen.nama_lengkap,
                        dosen_id
                    ): task_data
                    for task_data in pdf_processing_tasks
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_task):
                    task_data = future_to_task[future]
                    try:
                        success, pdf_data, mahasiswa_email, error_msg = future.result()
                        
                        if success:
                            pdf_processing_data.append({
                                'permohonan_id': task_data['permohonan_id'],
                                'pdf_data': pdf_data
                            })
                            
                            results['success'].append({
                                'id': task_data['permohonan_id'],
                                'judul': task_data['permohonan_judul']
                            })
                            
                            # Collect email info
                            if mahasiswa_email:
                                if mahasiswa_email not in emails_to_send:
                                    emails_to_send[mahasiswa_email] = {
                                        'nama': task_data['mahasiswa_nama'],
                                        'permohonan_list': []
                                    }
                                emails_to_send[mahasiswa_email]['permohonan_list'].append({
                                    'judul': task_data['permohonan_judul'],
                                    'jenis': task_data['jenis_nama']
                                })
                        else:
                            results['failed'].append({
                                'id': task_data['permohonan_id'],
                                'reason': error_msg or 'PDF processing failed'
                            })
                            
                    except Exception as e:
                        
                        results['failed'].append({
                            'id': task_data['permohonan_id'],
                            'reason': str(e)
                        })
            
            
            
            # ===== BATCH DATABASE UPDATE =====
            if pdf_processing_data:
                try:
                    # Get fresh permohonan objects for update
                    permohonan_map = {p.id: p for p in validated_permohonan}
                    
                    for item in pdf_processing_data:
                        permohonan = permohonan_map[item['permohonan_id']]
                        pdf_data = item['pdf_data']
                        
                        # Update permohonan
                        permohonan.status_permohonan = 'ditandatangani'
                        permohonan.signed_at = pdf_data['signed_at']
                        permohonan.file_signed_path = pdf_data['signed_path']
                        permohonan.qr_code_path = pdf_data['qr_filename']
                        permohonan.qr_code_data = pdf_data['qr_data_string']
                        
                        # Delete original file
                        from utils.file_utils import delete_file
                        if permohonan.file_path:
                            delete_file(permohonan.file_path)
                    
                    # Single commit for all changes
                    db.session.commit()
                    
                    
                except Exception as e:
                    db.session.rollback()
                    
                    # Mark all as failed
                    for item in pdf_processing_data:
                        # Find and remove from success
                        for success_item in results['success'][:]:
                            if success_item['id'] == item['permohonan_id']:
                                results['success'].remove(success_item)
                                break
                        
                        results['failed'].append({
                            'id': item['permohonan_id'],
                            'reason': 'Database commit failed'
                        })
                    return results, None
            
            # ===== PARALLEL EMAIL SENDING (Background) =====
            if emails_to_send:
                # Send emails in background thread (non-blocking)
                thread = threading.Thread(
                    target=self._send_batch_notifications_parallel,
                    args=(app, emails_to_send, dosen.nama_lengkap)  # ✅ Pass app
                )
                thread.daemon = True
                thread.start()
                
            
            return results, None
            
        except Exception as e:
            db.session.rollback()
            
            import traceback
            
            return None, f"Failed to batch sign permohonan: {str(e)}"



    # Fungsi lainya
    def _add_signature_to_permohonan_pdf(self, permohonan, ttd_path, qr_filename, dosen_nama_lengkap):
        """Menambahkan tanda tangan ke PDF permohonan (optimized - no DB query)"""
        try:
            from utils.pdf_utils import add_signature_to_pdf, get_full_file_path
            
            # Path file asli
            original_pdf_path = get_full_file_path(permohonan.file_path, 'uploads')
            
            # Path tanda tangan
            signature_path = get_full_file_path(ttd_path, 'uploads')
            
            # Path QR code
            qr_path = get_full_file_path(qr_filename, 'qr_codes')
            
            # Generate nama file signed
            original_filename = os.path.basename(permohonan.file_path)
            name_without_ext = os.path.splitext(original_filename)[0]
            signed_filename = f"{name_without_ext}_signed.pdf"
            
            # Path untuk save
            ttd_folder = current_app.config['DOCUMENT_PERMOHONAN_TTD_PATH']
            signed_absolute_path = os.path.join(ttd_folder, signed_filename)
            
            # Path relatif untuk database
            relative_ttd_folder = os.path.relpath(ttd_folder, current_app.config['UPLOAD_SIGNED'])
            signed_relative_path = os.path.join(relative_ttd_folder, signed_filename)
            
            # Proses PDF
            success, error = add_signature_to_pdf(
                original_pdf_path,
                signature_path, 
                qr_path,
                signed_absolute_path,
                dosen_nama_lengkap
            )
            
            if not success:
                return None, f"Failed to add signature to PDF: {error}"
            
            return signed_relative_path, None
            
        except Exception as e:
            return None, f"Error processing PDF signature: {str(e)}"

    
    def _process_single_pdf_parallel_with_context(self, app, task_data: dict, ttd_path: str, 
                                                   dosen_nama_lengkap: str, dosen_id: str):
        """
        Process QR generation + PDF signing untuk single permohonan (thread-safe dengan app context)
        Returns: (success, pdf_data_dict, mahasiswa_email, error_msg)
        """
        # ✅ RUN dalam Flask app context
        with app.app_context():
            try:
                # Generate QR code
                signed_at = datetime.utcnow()
                qr_data = {
                    'permohonan_id': str(task_data['permohonan_id']),
                    'signed_by': dosen_id,
                    'signed_at': signed_at.isoformat(),
                    'request_by': {
                        'nama': task_data['mahasiswa_nama'],
                        'nomor_induk': task_data['mahasiswa_nomor_induk']
                    }
                }
                
                qr_filename, qr_data_string, qr_error = generate_qr_code(qr_data, task_data['permohonan_id'])
                if qr_error:
                    return False, None, None, f"QR generation failed: {qr_error}"
                
                # Create temporary permohonan-like object for PDF processing
                class TempPermohonan:
                    def __init__(self, file_path):
                        self.file_path = file_path
                
                temp_permohonan = TempPermohonan(task_data['file_path'])
                
                # Add signature to PDF
                signed_path, pdf_error = self._add_signature_to_permohonan_pdf(
                    temp_permohonan,
                    ttd_path,
                    qr_filename,
                    dosen_nama_lengkap
                )
                if pdf_error:
                    return False, None, None, pdf_error
                
                # Prepare data for batch DB update
                pdf_data = {
                    'signed_path': signed_path,
                    'signed_at': signed_at,
                    'qr_filename': qr_filename,
                    'qr_data_string': qr_data_string
                }
                
                mahasiswa_email = task_data['mahasiswa_email']
                
                
                return True, pdf_data, mahasiswa_email, None
                
            except Exception as e:
                
                import traceback
                
                return False, None, None, str(e)


    def _send_single_email_with_context(self, app, email: str, nama: str, dosen_name: str, permohonan_list: list):
        """
        Send single email dengan app context untuk ThreadPoolExecutor
        """
        with app.app_context():
            from utils.email_utils import send_batch_permohonan_email_sync
            return send_batch_permohonan_email_sync(email, nama, dosen_name, permohonan_list)


    def _send_batch_notifications_parallel(self, app, emails_to_send: dict, dosen_name: str):
        """
        Send batch email notifications in parallel (runs in background thread)
        Setiap task dibungkus dengan app.app_context() via wrapper
        """
        try:
            
            # Use ThreadPoolExecutor for parallel email sending
            max_workers = min(5, len(emails_to_send))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit tasks dengan wrapper yang include app context
                future_to_email = {
                    executor.submit(
                        self._send_single_email_with_context,  #  Wrapper function
                        app,  #  Pass app untuk context
                        email,
                        data['nama'],
                        dosen_name,
                        data['permohonan_list']
                    ): email
                    for email, data in emails_to_send.items()
                }
                
                success_count = 0
                failed_count = 0
                
                for future in as_completed(future_to_email):
                    email = future_to_email[future]
                    try:
                        status, err = future.result()
                        if status:
                            success_count += 1
                            
                        else:
                            failed_count += 1
                            
                    except Exception as e:
                        failed_count += 1
                        
            
            
            
        except Exception as e:
            
            import traceback
            

    def _add_signature_to_permohonan_pdf_single(self, permohonan, ttd_path, qr_filename,dosen_id:str):
        """Menambahkan tanda tangan ke PDF permohonan"""
        try:
            from utils.pdf_utils import add_signature_to_pdf, get_full_file_path
            
            # Path file asli
            original_pdf_path = get_full_file_path(permohonan.file_path,'uploads')
            
            # Path tanda tangan
            signature_path = get_full_file_path(ttd_path,'uploads')
            
            # Path QR code
            qr_path = get_full_file_path(qr_filename,'qr_codes')
            
            # Generate nama file signed
            original_filename = os.path.basename(permohonan.file_path)
            name_without_ext = os.path.splitext(original_filename)[0]
            signed_filename = f"{name_without_ext}_signed.pdf"
            
            # Path untuk save
            ttd_folder = current_app.config['DOCUMENT_PERMOHONAN_TTD_PATH']
            signed_absolute_path = os.path.join(ttd_folder, signed_filename)
            
            # Path relatif untuk database
            relative_ttd_folder = os.path.relpath(ttd_folder, current_app.config['UPLOAD_SIGNED'])
            signed_relative_path = os.path.join(relative_ttd_folder, signed_filename)

            from app.models.dosen_model import Dosen
            dosen = db.session.query(Dosen).filter_by(user_id=dosen_id).first()
            
            # Proses PDF
            success, error = add_signature_to_pdf(
                original_pdf_path,
                signature_path, 
                qr_path,
                signed_absolute_path,
                dosen.nama_lengkap
            )
            
            if not success:
                return f"Failed to add signature to PDF: {error}"
            
            # Update path di database
            permohonan.file_signed_path = signed_relative_path
            
            return None
            
        except Exception as e:
            return f"Error processing PDF signature: {str(e)}"



    #belom digunakan
    # def _create_history_record(self, permohonan: Permohonan, action: str, komentar: str = None):
    #     """Create history record"""
    #     history = History(
    #         permohonan_id=permohonan.id,
    #         id_jenis_permohonan=permohonan.id_jenis_permohonan,
    #         id_mahasiswa=permohonan.id_mahasiswa,
    #         id_dosen=permohonan.id_dosen,
    #         action=action,
    #         komentar_permohonan=komentar,
    #         signed_at=datetime.utcnow() if action == 'signed' else None
    #     )
    #     db.session.add(history)

    #belom digunakan
    # def approve_permohonan(self, permohonan_id: int, dosen_id: str):
    #     """Approve permohonan"""
    #     try:
    #         permohonan = self.permohonan_repo.get_by_id(permohonan_id)
    #         if not permohonan:
    #             return None, "Permohonan not found"
            
    #         if permohonan.id_dosen != dosen_id:
    #             return None, "Unauthorized to approve this permohonan"
            
    #         if permohonan.status_permohonan != 'pending':
    #             return None, "Permohonan cannot be approved"
            
    #         # Update status
    #         permohonan.status_permohonan = 'disetujui'
    #         permohonan.approved_at = datetime.utcnow()
    #         # permohonan.komentar = komentar
            
    #         # Create history record
    #         # self._create_history_record(permohonan, 'approved')
            
    #         db.session.commit()
            
    #         # Send notification to mahasiswa
    #         notify_permohonan_approved(permohonan)
            
    #         return permohonan, None
            
    #     except Exception as e:
    #         db.session.rollback()
    #         return None, str(e)