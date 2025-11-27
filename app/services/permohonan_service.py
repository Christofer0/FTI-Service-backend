import os
import time
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
from concurrent.futures import ThreadPoolExecutor, as_completed

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

    #0000
    def _send_batch_notifications_smart(self, emails_dict: dict, dosen_name: str):
        """
        Smart email handler - auto select best method based on count
        
        Logic:
        - 1-5 emails: Synchronous (simple, no threading overhead)
        - 6-20 emails: Parallel with 5 threads (balanced)
        - 21-50 emails: Parallel with 10 threads (faster)
        - 51+ emails: Batched parallel (avoid overwhelming mail server)
        """
        from utils.email_utils import send_batch_permohonan_email_sync
        
        total_emails = len(emails_dict)
        
        if total_emails == 0:
            print("  📧 No emails to send")
            return
        
        print(f"\n📧 Sending {total_emails} emails...")
        
        # Prepare email list
        emails_list = [
            {
                'email': email,
                'nama': data['nama'],
                'dosen_name': dosen_name,
                'permohonan_list': data['permohonan_list']
            }
            for email, data in emails_dict.items()
        ]
        
        # ==========================================
        # DECISION LOGIC
        # ==========================================
        
        if total_emails <= 5:
            # Small batch: SYNCHRONOUS (most stable)
            print(f"  📋 Mode: Synchronous (simple, {total_emails} emails)")
            self._send_emails_synchronous(emails_list)
            
        elif total_emails <= 20:
            # Medium batch: PARALLEL with 5 threads
            print(f"  🚀 Mode: Parallel (5 threads, {total_emails} emails)")
            self._send_emails_parallel(emails_list, max_workers=5)
            
        elif total_emails <= 50:
            # Large batch: PARALLEL with 10 threads
            print(f"  🚀 Mode: Parallel (10 threads, {total_emails} emails)")
            self._send_emails_parallel(emails_list, max_workers=10)
            
        else:
            # Very large batch: BATCHED PARALLEL with rate limiting
            print(f"  📦 Mode: Batched Parallel ({total_emails} emails)")
            self._send_emails_batched_parallel(emails_list)


    def _send_emails_synchronous(self, emails_list: list):
        """
        Send emails synchronously (1 by 1)
        Best for: 1-5 emails
        Pros: Most stable, no threading issues
        Cons: Slow for many emails
        """
        from utils.email_utils import send_batch_permohonan_email_sync
        
        success = 0
        failed = 0
        start_time = time.time()
        
        for idx, email_data in enumerate(emails_list, 1):
            try:
                status, err = send_batch_permohonan_email_sync(
                    email_data['email'],
                    email_data['nama'],
                    email_data['dosen_name'],
                    email_data['permohonan_list']
                )
                
                if status:
                    success += 1
                else:
                    failed += 1
                    print(f"    ❌ Failed to {email_data['email']}: {err}")
                    
            except Exception as e:
                failed += 1
                print(f"    ❌ Error sending to {email_data['email']}: {str(e)}")
        
        elapsed = time.time() - start_time
        print(f"  ✅ Synchronous complete: {success} sent, {failed} failed ({elapsed:.2f}s)")


    def _send_emails_parallel(self, emails_list: list, max_workers: int = 5):
        """
        Send emails in parallel with ThreadPoolExecutor
        Best for: 6-50 emails
        Pros: Faster than sync
        Cons: Need proper app context handling
        """
        from flask import current_app
        
        app = current_app._get_current_object()
        
        success = 0
        failed = 0
        start_time = time.time()
        
        # Use ThreadPoolExecutor for parallel sending
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    self._send_single_email_with_context,
                    app,
                    email_data['email'],
                    email_data['nama'],
                    email_data['dosen_name'],
                    email_data['permohonan_list']
                ): email_data['email']
                for email_data in emails_list
            }
            
            # Wait for completion
            for future in as_completed(futures):
                email = futures[future]
                try:
                    status, err = future.result(timeout=30)
                    if status:
                        success += 1
                    else:
                        failed += 1
                        print(f"    ❌ Failed to {email}: {err}")
                except Exception as e:
                    failed += 1
                    print(f"    ❌ Error sending to {email}: {str(e)}")
        
        elapsed = time.time() - start_time
        print(f"  ✅ Parallel complete: {success} sent, {failed} failed ({elapsed:.2f}s)")


    def _send_emails_batched_parallel(self, emails_list: list, batch_size: int = 20, max_workers: int = 10):
        """
        Send emails in batches with parallel processing
        Best for: 51+ emails
        Pros: Rate limiting, avoid spam detection
        Cons: Slower but safer
        """
        from flask import current_app
        
        app = current_app._get_current_object()
        
        total_emails = len(emails_list)
        total_success = 0
        total_failed = 0
        
        # Split into batches
        batches = [emails_list[i:i + batch_size] 
                for i in range(0, total_emails, batch_size)]
        
        print(f"  📦 Processing {len(batches)} batches of {batch_size} emails each")
        
        for batch_idx, batch in enumerate(batches, 1):
            print(f"\n  📧 Batch {batch_idx}/{len(batches)} ({len(batch)} emails)...")
            batch_start = time.time()
            
            success = 0
            failed = 0
            
            # Process batch in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._send_single_email_with_context,
                        app,
                        email_data['email'],
                        email_data['nama'],
                        email_data['dosen_name'],
                        email_data['permohonan_list']
                    ): email_data['email']
                    for email_data in batch
                }
                
                for future in as_completed(futures):
                    email = futures[future]
                    try:
                        status, err = future.result(timeout=30)
                        if status:
                            success += 1
                        else:
                            failed += 1
                            print(f"      ❌ Failed to {email}: {err}")
                    except Exception as e:
                        failed += 1
                        print(f"      ❌ Error: {str(e)}")
            
            total_success += success
            total_failed += failed
            
            batch_time = time.time() - batch_start
            print(f"    ✅ Batch {batch_idx}: {success} sent, {failed} failed ({batch_time:.2f}s)")
            
            # Rate limiting: wait between batches
            if batch_idx < len(batches):
                wait_time = 2  # 2 seconds between batches
                print(f"    ⏳ Waiting {wait_time}s before next batch...")
                time.sleep(wait_time)
        
        print(f"\n  ✅ All batches complete: {total_success} sent, {total_failed} failed")


    def _send_single_email_with_context(self, app, to_email: str, mahasiswa_name: str, 
                                        dosen_name: str, permohonan_list: list):
        """
        Send single email with proper Flask app context
        Thread-safe wrapper for parallel execution
        """
        with app.app_context():
            try:
                from utils.email_utils import send_batch_permohonan_email_sync
                
                status, err = send_batch_permohonan_email_sync(
                    to_email,
                    mahasiswa_name,
                    dosen_name,
                    permohonan_list
                )
                
                return status, err
                
            except Exception as e:
                return False, str(e)


    # ==========================================
    # UPDATE: Main batch_sign_permohonan
    # ==========================================

    def batch_sign_permohonan(self, permohonan_ids: list, dosen_id: str):
        """
        Batch sign optimized untuk 1 vCPU server
        WITH SMART EMAIL HANDLER
        """
        
        MAX_BATCH_SIZE = 100
        if len(permohonan_ids) > MAX_BATCH_SIZE:
            return None, f"Maximum {MAX_BATCH_SIZE} permohonan per batch. Please split into multiple batches."
        
        results = {
            'success': [],
            'failed': [],
            'total': len(permohonan_ids),
            'processing_time': 0
        }
        
        start_time = time.time()
        
        try:
            # Get dosen data once
            from app.models.dosen_model import Dosen
            dosen = db.session.query(Dosen).filter_by(user_id=dosen_id).first()
            if not dosen or not dosen.ttd_path:
                return None, "Dosen signature not found"
            
            # Process dalam chunks
            CHUNK_SIZE = 10
            chunks = [permohonan_ids[i:i + CHUNK_SIZE] 
                    for i in range(0, len(permohonan_ids), CHUNK_SIZE)]
            
            emails_to_send = {}
            
            print(f"\n📦 Processing {len(permohonan_ids)} permohonan in {len(chunks)} chunks")
            print(f"⚙️  Server mode: Sequential PDF + Smart Email (1 vCPU optimized)")
            
            # Process each chunk (EXISTING CODE - no change)
            for chunk_idx, chunk in enumerate(chunks, 1):
                print(f"\n🔄 Chunk {chunk_idx}/{len(chunks)} - Processing {len(chunk)} permohonan...")
                chunk_start = time.time()
                
                for permohonan_id in chunk:
                    try:
                        permohonan = self.permohonan_repo.get_by_id(permohonan_id)
                        
                        # Validasi (same as before)
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
                        
                        # Process signature
                        success, mahasiswa_data = self._process_single_signature_batch(
                            permohonan, dosen, dosen_id
                        )
                        
                        if success:
                            results['success'].append({
                                'id': permohonan_id,
                                'judul': permohonan.judul
                            })
                            
                            # Collect email info
                            if mahasiswa_data and mahasiswa_data['email']:
                                email = mahasiswa_data['email']
                                if email not in emails_to_send:
                                    emails_to_send[email] = {
                                        'nama': mahasiswa_data['nama'],
                                        'permohonan_list': []
                                    }
                                emails_to_send[email]['permohonan_list'].append({
                                    'judul': permohonan.judul,
                                    'jenis': mahasiswa_data['jenis']
                                })
                        else:
                            results['failed'].append({
                                'id': permohonan_id,
                                'reason': 'Signature processing failed'
                            })
                            
                    except Exception as e:
                        print(f"  ❌ Error processing {permohonan_id}: {str(e)}")
                        results['failed'].append({
                            'id': permohonan_id,
                            'reason': str(e)
                        })
                        continue
                
                # Commit per chunk
                try:
                    db.session.commit()
                    chunk_time = time.time() - chunk_start
                    print(f"  ✅ Chunk {chunk_idx} committed in {chunk_time:.2f}s")
                except Exception as e:
                    db.session.rollback()
                    print(f"  ❌ Chunk {chunk_idx} rollback: {str(e)}")
                
                # Delay between chunks
                if chunk_idx < len(chunks):
                    time.sleep(1)
            
            # Send emails with SMART handler
            if emails_to_send:
                self._send_batch_notifications_smart(emails_to_send, dosen.nama_lengkap)
            
            results['processing_time'] = round(time.time() - start_time, 2)
            
            print(f"\n✅ Batch signing completed!")
            print(f"   Success: {len(results['success'])}")
            print(f"   Failed: {len(results['failed'])}")
            print(f"   Total time: {results['processing_time']}s")
            
            return results, None
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Batch signing failed, rolled back: {str(e)}")
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
            # mahasiswa_email = mahasiswa.user.email if mahasiswa.user else None
            # return True, mahasiswa_email
            return True, {
                'email': mahasiswa.user.email if mahasiswa.user else None,
                'nama': mahasiswa.user.nama if mahasiswa.user else None,
                'jenis': permohonan.jenis_permohonan if hasattr(permohonan, 'jenis_permohonan') else None
            }

            
        except Exception as e:
            print(f"❌ Error processing signature for permohonan {permohonan.id}: {str(e)}")
            return False, None