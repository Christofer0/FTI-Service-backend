# utils/maintenance_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
import os
from flask_mail import Message
from extensions import db, mail
from app.models.permohonan_model import Permohonan
from flask import current_app

# Inisialisasi scheduler dengan timezone Jakarta
scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Jakarta"))


def delete_old_signed_files():
    """
    Hapus file PDF yang sudah ditandatangani lebih dari 2 bulan
    dan update file_signed_path jadi 'expired'
    """
    try:
        print("=" * 80)
        print(f"🚀 [MAINTENANCE] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Hitung cutoff date (2 bulan yang lalu)
        cutoff_date = datetime.utcnow() - timedelta(days=60)
        print(f"📅 Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Query permohonan yang sudah ditandatangani > 2 bulan
        permohonan_list = Permohonan.query.filter(
            Permohonan.status_permohonan == 'ditandatangani',
            Permohonan.file_signed_path.isnot(None),
            Permohonan.file_signed_path != '',
            Permohonan.file_signed_path != 'expired',
            Permohonan.signed_at < cutoff_date
        ).all()
        
        print(f"🔍 Found {len(permohonan_list)} files to delete")
        
        if len(permohonan_list) == 0:
            print("✅ No files to delete")
            print("=" * 80)
            return
        
        deleted_count = 0
        failed_count = 0
        deleted_files = []
        failed_files = []
        
        # Process setiap permohonan
        for permohonan in permohonan_list:
            try:
                file_path = permohonan.file_signed_path
                
                # Build full path ke file
                full_path = os.path.join(
                    current_app.config['UPLOAD_SIGNED'],
                    file_path
                )
                
                print(f"🗑️  Deleting: {file_path}")
                
                # Cek apakah file exists
                if os.path.exists(full_path):
                    # Hapus file
                    os.remove(full_path)
                    print(f"   ✅ File deleted")
                else:
                    print(f"   ⚠️  File not found (will update DB anyway)")
                
                # Update database: set file_signed_path jadi 'expired'
                permohonan.file_signed_path = 'expired'
                
                deleted_count += 1
                deleted_files.append({
                    'id': permohonan.id,
                    'judul': permohonan.judul,
                    'file': file_path,
                    'signed_at': permohonan.signed_at.strftime('%Y-%m-%d')
                })
                
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                print(f"   ❌ Failed: {error_msg}")
                failed_files.append({
                    'id': permohonan.id,
                    'file': permohonan.file_signed_path,
                    'error': error_msg
                })
        
        # Commit semua perubahan database
        db.session.commit()
        print(f"💾 Database updated")
        
        # Summary
        print(f"")
        print(f"📊 SUMMARY:")
        print(f"   ✅ Deleted: {deleted_count} files")
        print(f"   ❌ Failed: {failed_count} files")
        print("=" * 80)
        
        # Kirim email report ke admin
        send_maintenance_report(deleted_count, failed_count, deleted_files, failed_files)
        
    except Exception as e:
        print(f"❌ [ERROR] Maintenance failed: {str(e)}")
        db.session.rollback()


def send_maintenance_report(deleted_count, failed_count, deleted_files, failed_files):
    """Kirim email report hasil maintenance ke admin"""
    try:
        admin_email = current_app.config.get('ADMIN_EMAIL')
        if not admin_email:
            print("⚠️  ADMIN_EMAIL not configured, skipping email report")
            return
        
        now = datetime.now()
        subject = f"🔧 Maintenance Report - {now.strftime('%d %b %Y')}"
        
        # Build list file yang dihapus
        deleted_list = ""
        if deleted_files:
            for item in deleted_files[:15]:  # Show max 15
                deleted_list += f"""
                <li style="margin-bottom: 8px; font-size: 14px;">
                    <strong>ID {item['id']}:</strong> {item['judul']}<br>
                    <small style="color: #6b7280;">File: {item['file']} | Signed: {item['signed_at']}</small>
                </li>
                """
            if len(deleted_files) > 15:
                deleted_list += f"<li><em>...dan {len(deleted_files) - 15} file lainnya</em></li>"
        else:
            deleted_list = "<li><em>Tidak ada file yang dihapus</em></li>"
        
        # Build list file yang gagal
        failed_list = ""
        if failed_files:
            for item in failed_files:
                failed_list += f"""
                <li style="margin-bottom: 8px; font-size: 14px; color: #dc2626;">
                    <strong>ID {item['id']}:</strong> {item['file']}<br>
                    <small>Error: {item['error']}</small>
                </li>
                """
        
        status_color = "#10b981" if failed_count == 0 else "#f59e0b"
        status_icon = "✅" if failed_count == 0 else "⚠️"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #374151;">
            <div style="max-width: 700px; margin: auto; padding: 20px; 
                        border: 1px solid #e5e7eb; border-radius: 10px;">
                
                <div style="background: {status_color}; padding: 20px; border-radius: 8px; 
                            text-align: center; margin-bottom: 20px;">
                    <h2 style="color: white; margin: 0;">{status_icon} Maintenance Report</h2>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 14px;">
                        Auto-delete Old Signed Files
                    </p>
                </div>
                
                <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #1f2937;">📊 Ringkasan</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                                ✅ File Berhasil Dihapus
                            </td>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; 
                                       text-align: right; font-weight: bold; color: #10b981;">
                                {deleted_count} files
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                                ❌ File Gagal Dihapus
                            </td>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; 
                                       text-align: right; font-weight: bold; color: #dc2626;">
                                {failed_count} files
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px;">📁 Total Diproses</td>
                            <td style="padding: 10px; text-align: right; font-weight: bold;">
                                {deleted_count + failed_count} files
                            </td>
                        </tr>
                    </table>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #1f2937;">🗑️ File yang Dihapus</h3>
                    <ul style="list-style: none; padding: 0;">
                        {deleted_list}
                    </ul>
                </div>
                
                {f'''
                <div style="background: #fef2f2; padding: 15px; border-left: 4px solid #dc2626; 
                            border-radius: 6px; margin-bottom: 20px;">
                    <h3 style="color: #dc2626; margin-top: 0;">⚠️ File yang Gagal</h3>
                    <ul style="list-style: none; padding: 0;">
                        {failed_list}
                    </ul>
                </div>
                ''' if failed_files else ''}
                
                <div style="background: #eff6ff; padding: 15px; border-left: 4px solid #3b82f6; 
                            border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #1e40af;">
                        <strong>ℹ️ Informasi:</strong><br>
                        Maintenance berjalan otomatis setiap tanggal <strong>1</strong> pada jam <strong>02:00 WIB</strong>.<br>
                        File yang sudah lebih dari <strong>2 bulan</strong> sejak ditandatangani akan otomatis dihapus.
                    </p>
                </div>
                
                <p>Salam,<br><strong>Sistem Maintenance</strong></p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin-top: 30px;">
                <p style="font-size: 12px; text-align: center; color: #9ca3af;">
                    Email otomatis dari Sistem Tanda Tangan Digital<br>
                    {now.strftime('%A, %d %B %Y - %H:%M:%S')} WIB<br>
                    Jangan balas email ini
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
Maintenance Report - {now.strftime('%d %B %Y')}

RINGKASAN:
✅ File Berhasil Dihapus: {deleted_count}
❌ File Gagal Dihapus: {failed_count}
📁 Total Diproses: {deleted_count + failed_count}

Maintenance berjalan otomatis setiap tanggal 1 jam 02:00 WIB.

Salam,
Sistem Maintenance
        """
        
        msg = Message(
            subject,
            recipients=[admin_email],
            body=plain_body,
            html=html_body
        )
        mail.send(msg)
        print(f"📧 Maintenance report sent to {admin_email}")
        
    except Exception as e:
        print(f"❌ [ERROR] Failed to send maintenance report: {str(e)}")


def start_maintenance_scheduler(app):
    """
    Inisialisasi APScheduler untuk maintenance
    Berjalan setiap tanggal 1 jam 02:00 WIB
    """
    # Bungkus fungsi job agar memiliki app_context dari Flask
    def job_wrapper():
        with app.app_context():
            delete_old_signed_files()
    
    # Jadwalkan job: setiap tanggal 1, jam 02:00 WIB
    scheduler.add_job(
        func=job_wrapper,
        trigger='cron',
        day=1,              # Tanggal 1 setiap bulan
        hour=2,             # Jam 02:00 WIB
        minute=0,
        timezone=pytz.timezone("Asia/Jakarta"),
        id='delete_old_signed_files',
        replace_existing=True
    )
    
    scheduler.start()
    