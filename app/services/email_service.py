from flask_mail import Message
from extensions import mail
from flask import current_app, render_template_string
import threading


def _send_async_email(app, msg):
    """Helper function to send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"❌ Email send error: {str(e)}")
            pass


def send_async_email(msg):
    """Send email in background thread"""
    app = current_app._get_current_object()
    thread = threading.Thread(target=_send_async_email, args=(app, msg))
    thread.start()


def send_otp_email(email, otp_code, nama=None, role=None):
    """
    Send OTP verification email
    
    Args:
        email: Recipient email
        otp_code: 6-digit OTP code
        nama: User name (optional)
        role: User role (mahasiswa/dosen/admin)
    """
    
    # Determine greeting based on role
    role_text = {
        'mahasiswa': 'Mahasiswa',
        'dosen': 'Dosen',
        'admin': 'Administrator'
    }.get(role, 'Pengguna')
    
    greeting = f"Halo {nama}," if nama else f"Halo {role_text},"
    
    # HTML Email Template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 18px;
                color: #333;
                margin-bottom: 20px;
            }}
            .message {{
                font-size: 16px;
                color: #555;
                line-height: 1.6;
                margin-bottom: 30px;
            }}
            .otp-box {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 8px;
                padding: 25px;
                text-align: center;
                margin: 30px 0;
            }}
            .otp-label {{
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .otp-code {{
                font-size: 36px;
                font-weight: 700;
                color: white;
                letter-spacing: 8px;
                font-family: 'Courier New', monospace;
            }}
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .warning p {{
                margin: 0;
                color: #856404;
                font-size: 14px;
            }}
            .expiry {{
                color: #666;
                font-size: 14px;
                text-align: center;
                margin-top: 20px;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px 30px;
                text-align: center;
                color: #6c757d;
                font-size: 13px;
                border-top: 1px solid #e9ecef;
            }}
            .footer p {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Verifikasi Email</h1>
            </div>
            
            <div class="content">
                <p class="greeting">{greeting}</p>
                
                <p class="message">
                    Terima kasih telah mendaftar di <strong>FTI-Service UKSW</strong>. 
                    Untuk melanjutkan proses registrasi, silakan masukkan kode OTP berikut:
                </p>
                
                <div class="otp-box">
                    <div class="otp-label">Kode Verifikasi OTP</div>
                    <div class="otp-code">{otp_code}</div>
                </div>
                
                <div class="warning">
                    <p>⚠️ <strong>Penting:</strong></p>
                    <p>• Jangan bagikan kode ini kepada siapa pun</p>
                    <p>• Kode ini hanya berlaku selama 10 menit</p>
                    <p>• Jika Anda tidak meminta kode ini, abaikan email ini</p>
                </div>
                
                <p class="expiry">
                    ⏱️ Kode OTP akan kadaluarsa dalam <strong>10 menit</strong>
                </p>
            </div>
            
            <div class="footer">
                <p><strong>FTI-Service UKSW</strong></p>
                <p>Fakultas Teknologi Informasi</p>
                <p>Universitas Kristen Satya Wacana</p>
                <p style="margin-top: 15px; color: #999; font-size: 12px;">
                    Email ini dikirim secara otomatis, mohon tidak membalas email ini.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version (fallback)
    text_body = f"""
    {greeting}
    
    Terima kasih telah mendaftar di FTI-Service UKSW.
    
    Kode OTP Anda: {otp_code}
    
    Kode ini berlaku selama 10 menit.
    Jangan bagikan kode ini kepada siapa pun.
    
    Jika Anda tidak meminta kode ini, abaikan email ini.
    
    ---
    FTI-Service UKSW
    Fakultas Teknologi Informasi
    Universitas Kristen Satya Wacana
    """
    
    # Create message
    msg = Message(
        subject='[FTI-Service] Kode Verifikasi OTP',
        recipients=[email],
        body=text_body,
        html=html_body
    )
    
    # Send async
    send_async_email(msg)
    
    return True


def send_welcome_email(email, nama, role):
    """Send welcome email after successful registration"""
    
    role_text = {
        'mahasiswa': 'Mahasiswa',
        'dosen': 'Dosen',
        'admin': 'Administrator'
    }.get(role, 'Pengguna')
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 12px 12px 0 0;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Selamat Datang!</h1>
            </div>
            <div class="content">
                <p>Halo <strong>{nama}</strong>,</p>
                <p>Registrasi Anda sebagai <strong>{role_text}</strong> di FTI-Service UKSW telah berhasil!</p>
                <p>Anda sekarang dapat login dan menggunakan layanan kami.</p>
                <p>Terima kasih telah bergabung! 🚀</p>
            </div>
            <div class="footer">
                <p><strong>FTI-Service UKSW</strong></p>
                <p>Fakultas Teknologi Informasi</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = Message(
        subject='[FTI-Service] Selamat Datang!',
        recipients=[email],
        html=html_body
    )
    
    send_async_email(msg)
    return True