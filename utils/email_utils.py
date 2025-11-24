# utils/email_utils.py

from flask_mail import Message
from extensions import mail
from flask import current_app
from datetime import datetime
import threading
import os

def _send_async_email(app, msg):
    """Helper untuk kirim email async"""
    with app.app_context():
        mail.send(msg)

def send_permohonan_email(mahasiswa_email, mahasiswa_nama, dosen_nama, status_permohonan, alasan_penolakan=None):
    """Send single permohonan status notification email (HTML styled)"""
    try:
        # Ambil app context (wajib untuk threading)
        app = current_app._get_current_object()
        now = datetime.now()

        status_lower = status_permohonan.lower()
        is_signed = status_lower == "ditandatangani"

        # Warna & ikon berdasarkan status
        icon = "✅" if is_signed else "❌"
        color = "#10b981" if is_signed else "#ef4444"
        box_bg = "#ecfdf5" if is_signed else "#fef2f2"

        subject = f"Status Permohonan Anda: {status_permohonan.capitalize()} - {now.strftime('%d %b %Y')}"

        # =============================
        # HTML Email Body
        # =============================
        alasan_html = (
            f"""
            <div style="margin-top: 10px; padding: 12px; background:#fef2f2; border-left:4px solid #dc2626; border-radius:6px;">
                <strong style="color:#b91c1c;">Alasan Penolakan:</strong><br>
                <span style="color:#7f1d1d;">{alasan_penolakan}</span>
            </div>
            """
            if not is_signed and alasan_penolakan
            else ""
        )

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border:1px solid #ddd; border-radius:12px; background:white;">

                <div style="text-align:center; margin-bottom:20px;">
                    <h2 style="color:{color}; margin:0;">{icon} Permohonan Anda {status_permohonan.capitalize()}</h2>
                </div>

                <p>Halo <strong>{mahasiswa_nama}</strong>,</p>

                <div style="background:{box_bg}; padding:15px; border-left:4px solid {color}; border-radius:6px;">
                    <p style="margin:0;">
                        Dosen: <strong>{dosen_nama}</strong><br>
                        Status: <strong style="color:{color};">{status_permohonan.capitalize()}</strong><br>
                        Tanggal: {now.strftime('%A, %d %B %Y')}
                    </p>
                </div>

                {alasan_html}

                <p style="margin-top:25px;">
                    {"Silakan cek aplikasi untuk melihat dokumen Anda." if is_signed else "Silakan lakukan revisi di aplikasi."}
                </p>

                <div style="text-align:center; margin-top:30px;">
                    <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/mahasiswa/history"
                       style="background:#3b82f6; color:white; padding:14px 32px; text-decoration:none; border-radius:8px; font-weight:600;">
                        Buka Aplikasi
                    </a>
                </div>

                <hr style="margin:30px 0; border:none; border-top:1px solid #e5e7eb;">
                <p style="font-size:12px; color:#9ca3af; text-align:center; margin:0;">
                    Email otomatis dari Sistem Tanda Tangan Digital<br>
                    Tanggal: {now.strftime('%A, %d %B %Y')}<br>
                    Jangan balas email ini
                </p>
            </div>
        </body>
        </html>
        """

        # =============================
        # Plain text fallback
        # =============================
        plain_body = f"""Halo {mahasiswa_nama},

Dosen: {dosen_nama}
Status: {status_permohonan.capitalize()}
Tanggal: {now.strftime('%A, %d %B %Y')}

"""

        if not is_signed and alasan_penolakan:
            plain_body += f"Alasan Penolakan: {alasan_penolakan}\n\n"

        plain_body += (
            "Silakan cek aplikasi untuk melihat dokumen Anda."
            if is_signed
            else "Silakan lakukan revisi di aplikasi."
        )

        # Create Email Message
        msg = Message(
            subject=subject,
            recipients=[mahasiswa_email],
            body=plain_body,
            html=html_body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )

        # Kirim email async
        thread = threading.Thread(target=_send_async_email, args=(app, msg))
        thread.start()

        return True, None

    except Exception as e:
        print(f"❌ Email send error: {str(e)}")
        return False, str(e)


# def send_permohonan_email(mahasiswa_email, mahasiswa_nama, dosen_nama, status_permohonan, alasan_penolakan=None):
#     """Send single permohonan status notification email"""
#     try:
#         # Ambil app context (wajib untuk threading)
#         app = current_app._get_current_object()
#         now = datetime.now()

#         subject = f"Status Permohonan Anda {status_permohonan.capitalize()} - {now.strftime('%d %b %Y')}"

#         if status_permohonan.lower() == "ditandatangani":
#             body = (
#                 f"Halo {mahasiswa_nama},\n\n"
#                 f"Dosen: {dosen_nama} ✅\n"
#                 f"Tanggal: {now.strftime('%A, %d %B %Y')}\n\n"
#                 f"Silakan cek aplikasi untuk melihat dokumen Anda.\n\n"
#                 f"Terima kasih."
#             )
#         else:
#             alasan_text = f"Alasan Penolakan: {alasan_penolakan}\n\n" if alasan_penolakan else ""
#             body = (
#                 f"Halo {mahasiswa_nama},\n\n"
#                 f"Dosen: {dosen_nama} ❌\n"
#                 f"{alasan_text}"
#                 f"Tanggal: {now.strftime('%A, %d %B %Y')}\n\n"
#                 f"Silakan lakukan revisi di aplikasi.\n\n"
#                 f"Terima kasih."
#             )

#         msg = Message(
#             subject=subject,
#             recipients=[mahasiswa_email],
#             body=body,
#             sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
#         )

#         # Kirim email di background (tidak bikin API lemot)
#         thread = threading.Thread(target=_send_async_email, args=(app, msg))
#         thread.start()

#         return True, None

#     except Exception as e:
#         print(f"❌ Email send error: {str(e)}")
#         return False, str(e)


def send_batch_permohonan_email(to_email: str, mahasiswa_name: str, dosen_name: str, permohonan_list: list):
    """Send batch signed notification email"""
    try:
        # Ambil app context (wajib untuk threading)
        app = current_app._get_current_object()
        now = datetime.now()
        
        subject = f"✅ {len(permohonan_list)} Permohonan Ditandatangani - {now.strftime('%d %b %Y')}"
        
        # Build permohonan list HTML
        permohonan_items = ""
        for idx, p in enumerate(permohonan_list, 1):
            permohonan_items += f"""
            <li style="margin-bottom: 12px; padding: 10px; background: #f3f4f6; border-radius: 6px;">
                <strong style="color: #1f2937;">{idx}. {p['judul']}</strong><br>
                <small style="color: #6b7280;">Jenis: {p['jenis']}</small>
            </li>
            """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #ffffff;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #10b981; margin: 0;">🎉 Permohonan Ditandatangani</h2>
                </div>
                
                <p>Halo <strong>{mahasiswa_name}</strong>,</p>
                
                <p>Kabar baik! Dosen <strong>{dosen_name}</strong> telah menandatangani <strong style="color: #3b82f6;">{len(permohonan_list)} permohonan</strong> Anda:</p>
                
                <ul style="padding: 0; list-style: none;">
                    {permohonan_items}
                </ul>
                
                <div style="background: #eff6ff; padding: 15px; border-left: 4px solid #3b82f6; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #1e40af;">
                        <strong>📥 Download Dokumen:</strong><br>
                        Anda sekarang dapat mengunduh dokumen yang telah ditandatangani melalui sistem.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/mahasiswa/history" 
                       style="background: #3b82f6; color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: 600;">
                        Lihat History Permohonan Saya
                    </a>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                
                <p style="font-size: 12px; color: #9ca3af; text-align: center; margin: 0;">
                    Email otomatis dari Sistem Tanda Tangan Digital<br>
                    Tanggal: {now.strftime('%A, %d %B %Y')}<br>
                    Jangan balas email ini
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        plain_body = f"""
Halo {mahasiswa_name},

Kabar baik! Dosen {dosen_name} telah menandatangani {len(permohonan_list)} permohonan Anda:

"""
        for idx, p in enumerate(permohonan_list, 1):
            plain_body += f"{idx}. {p['judul']} (Jenis: {p['jenis']})\n"
        
        plain_body += f"""
Tanggal: {now.strftime('%A, %d %B %Y')}

Anda sekarang dapat mengunduh dokumen yang telah ditandatangani melalui sistem.

Terima kasih.
        """
        
        # Create message dengan HTML dan plain text
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=plain_body,  # Plain text fallback
            html=html_body,   # HTML version
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )
        
        # Kirim email di background (tidak bikin API lemot)
        thread = threading.Thread(target=_send_async_email, args=(app, msg))
        thread.start()
        
        print(f"✅ Batch email queued to {to_email} ({len(permohonan_list)} permohonan)")
        return True, None
        
    except Exception as e:
        print(f"❌ Batch email send error: {str(e)}")
        return False, str(e)