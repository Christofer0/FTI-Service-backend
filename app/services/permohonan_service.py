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
            self._create_history_record(permohonan, 'created')
            
            db.session.commit()
            
            # Send notification to dosen
            # notify_permohonan_created(permohonan)
            
            return permohonan, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    def approve_permohonan(self, permohonan_id: int, dosen_id: str):
        """Approve permohonan"""
        try:
            permohonan = self.permohonan_repo.get_by_id(permohonan_id)
            if not permohonan:
                return None, "Permohonan not found"
            
            if permohonan.id_dosen != dosen_id:
                return None, "Unauthorized to approve this permohonan"
            
            if permohonan.status_permohonan != 'pending':
                return None, "Permohonan cannot be approved"
            
            # Update status
            permohonan.status_permohonan = 'disetujui'
            permohonan.approved_at = datetime.utcnow()
            # permohonan.komentar = komentar
            
            # Create history record
            self._create_history_record(permohonan, 'approved')
            
            db.session.commit()
            
            # Send notification to mahasiswa
            notify_permohonan_approved(permohonan)
            
            return permohonan, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    def reject_permohonan(self, permohonan_id: int, dosen_id: str, komentar_penolakan: str):
        """Reject permohonan"""
        try:
            permohonan = self.permohonan_repo.get_by_id(permohonan_id)
            print("tplak",permohonan)
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
            if not status:
                print("Email send error:", err)
            
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
            signed_pdf_error = self._add_signature_to_permohonan_pdf(
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
            if not status:
                print("Email send error:", err)
      
            return permohonan, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
        
    def _add_signature_to_permohonan_pdf(self, permohonan, ttd_path, qr_filename,dosen_id:str):
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
    
    def _create_history_record(self, permohonan: Permohonan, action: str, komentar: str = None):
        """Create history record"""
        history = History(
            permohonan_id=permohonan.id,
            id_jenis_permohonan=permohonan.id_jenis_permohonan,
            id_mahasiswa=permohonan.id_mahasiswa,
            id_dosen=permohonan.id_dosen,
            action=action,
            komentar_permohonan=komentar,
            signed_at=datetime.utcnow() if action == 'signed' else None
        )
        db.session.add(history)

    def get_permohonan_dosen(self, dosen_id: str, status: str = None, jenis_id: int = None):
        """Get permohonan untuk halaman dosen"""
        return self.permohonan_repo.get_by_dosen_with_filter(dosen_id, status, jenis_id)
    


    # app/services/permohonan_service.py
    def batch_sign_permohonan(self, permohonan_ids: list, dosen_id: str):
        """Batch sign multiple permohonan dengan efficient processing"""
        results = {
            'success': [],
            'failed': [],
            'total': len(permohonan_ids)
        }
        
        try:
            # Get dosen data once (optimization)
            from app.models.dosen_model import Dosen
            dosen = db.session.query(Dosen).filter_by(user_id=dosen_id).first()
            if not dosen or not dosen.ttd_path:
                return None, "Dosen signature not found"
            
            # Collect emails for batch notification
            emails_to_send = {}
            
            # Process each permohonan
            for permohonan_id in permohonan_ids:
                try:
                    permohonan = self.permohonan_repo.get_by_id(permohonan_id)
                    
                    # Validasi
                    if not permohonan:
                        results['failed'].append({
                            'id': permohonan_id,
                            'reason': 'Permohonan not found'
                        })
                        continue
                    
                    if permohonan.id_dosen != dosen_id:
                        results['failed'].append({
                            'id': permohonan_id,
                            'reason': 'Unauthorized - not your permohonan'
                        })
                        continue
                    
                    if permohonan.status_permohonan not in ['pending', 'disetujui']:
                        results['failed'].append({
                            'id': permohonan_id,
                            'reason': f'Cannot sign (status: {permohonan.status_permohonan})'
                        })
                        continue
                    
                    if not permohonan.file_path:
                        results['failed'].append({
                            'id': permohonan_id,
                            'reason': 'No file attached'
                        })
                        continue
                    
                    # Process signature (tanpa commit individual)
                    success, mahasiswa_email = self._process_single_signature_batch(
                        permohonan, dosen, dosen_id
                    )
                    
                    if success:
                        results['success'].append({
                            'id': permohonan_id,
                            'judul': permohonan.judul
                        })
                        
                        # Collect email info
                        if mahasiswa_email:
                            if mahasiswa_email not in emails_to_send:
                                emails_to_send[mahasiswa_email] = {
                                    'nama': permohonan.mahasiswa.user.nama,
                                    'permohonan_list': []
                                }
                            emails_to_send[mahasiswa_email]['permohonan_list'].append({
                                'judul': permohonan.judul,
                                'jenis': permohonan.jenis_permohonan.nama_jenis_permohonan if permohonan.jenis_permohonan else '-'
                            })
                    else:
                        results['failed'].append({
                            'id': permohonan_id,
                            'reason': 'Signature processing failed'
                        })
                        
                except Exception as e:
                    print(f"❌ Error processing permohonan {permohonan_id}: {str(e)}")
                    results['failed'].append({
                        'id': permohonan_id,
                        'reason': str(e)
                    })
                    continue
            
            # Commit all changes at once
            db.session.commit()
            print(f"✅ Batch commit successful: {len(results['success'])} permohonan")
            
            # Send batch email notifications
            if emails_to_send:
                self._send_batch_notifications(emails_to_send, dosen.nama_lengkap)
            
            return results, None
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Batch signing failed, rolled back: {str(e)}")
            return None, f"Failed to batch sign permohonan: {str(e)}"


    def _process_single_signature_batch(self, permohonan, dosen, dosen_id: str):
        """Process signature untuk single permohonan dalam batch (tanpa commit)"""
        try:
            # Get mahasiswa data
            from app.models.mahasiswa_model import Mahasiswa
            mahasiswa = db.session.query(Mahasiswa).filter_by(user_id=permohonan.id_mahasiswa).first()
            if not mahasiswa:
                return False, None
            
            # Generate QR code
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
                print(f"❌ QR generation failed for {permohonan.id}: {qr_error}")
                return False, None
            
            # Add signature to PDF
            signed_pdf_error = self._add_signature_to_permohonan_pdf(
                permohonan, 
                dosen.ttd_path, 
                qr_filename,
                dosen_id
            )
            if signed_pdf_error:
                print(f"❌ PDF signing failed for {permohonan.id}: {signed_pdf_error}")
                return False, None
            
            # Update status (tanpa commit - akan di-commit batch)
            permohonan.status_permohonan = 'ditandatangani'
            permohonan.signed_at = datetime.utcnow()
            permohonan.qr_code_path = qr_filename
            permohonan.qr_code_data = qr_data_string
            
            # Delete original file
            from utils.file_utils import delete_file
            if permohonan.file_path:
                delete_file(permohonan.file_path)
            
            # Return mahasiswa email for batch notification
            mahasiswa_email = mahasiswa.user.email if mahasiswa.user else None
            return True, mahasiswa_email
            
        except Exception as e:
            print(f"❌ Error processing signature for permohonan {permohonan.id}: {str(e)}")
            return False, None


    def _send_batch_notifications(self, emails_to_send: dict, dosen_name: str):
        """Send batch email notifications"""
        from utils.email_utils import send_batch_permohonan_email
        
        for email, data in emails_to_send.items():
            try:
                status, err = send_batch_permohonan_email(
                    email,
                    data['nama'],
                    dosen_name,
                    data['permohonan_list']
                )
                if not status:
                    print(f"❌ Email send failed to {email}: {err}")
                else:
                    print(f"✅ Batch email sent to {email}")
            except Exception as e:
                print(f"❌ Error sending email to {email}: {str(e)}")