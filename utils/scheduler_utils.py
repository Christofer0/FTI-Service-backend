from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
from flask_mail import Message
from extensions import db, mail
from app.models.permohonan_model import Permohonan
from app.models.dosen_model import Dosen
from app.models.user_model import User

# Inisialisasi scheduler dengan timezone Jakarta
scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Jakarta"))


def send_weekly_pending_notifications():

    # Ambil semua dosen
    dosen_list = User.query.filter_by(role="dosen").all()

    for dosen in dosen_list:
        if not dosen.email:
            continue
        
        # Hitung pending milik dosen
        jumlah_pending = (
            Permohonan.query
            .filter_by(id_dosen=dosen.id, status_permohonan="pending")
            .count()
        )

        if jumlah_pending == 0:
            continue  

        subject = f"⏳ Pengingat Permohonan Pending - {datetime.now().strftime('%d %b %Y')}"

        # 🎨 HTML yang lebih menarik (tanpa mengubah logika)
        html_body = f"""
        <html>
        <body style="font-family: Arial; color: #374151;">
            <div style="max-width: 600px; margin: auto; padding: 20px; 
                        border: 1px solid #e5e7eb; border-radius: 10px;">

                <h2 style="color: #f59e0b; text-align: center; margin-top: 0;">
                    ⏳ Pengingat Permohonan Pending
                </h2>

                <p>
                    Halo <strong>{dosen.nama}</strong>,
                </p>

                <p>
                    Anda memiliki 
                    <strong style="color: #ef4444;">{jumlah_pending} permohonan pending</strong>
                    yang menunggu untuk ditinjau.
                </p>

                <div style="background: #fef3c7; padding: 12px; border-left: 4px solid #f59e0b;
                            border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0; color: #92400e;">
                        Mohon segera melakukan pengecekan agar proses mahasiswa tidak tertunda.
                    </p>
                </div>

                <p>Salam,<br><strong>FTI-Service</strong></p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin-top: 30px;">
                <p style="font-size: 12px; text-align: center; color: #9ca3af;">
                    Email otomatis — jangan dibalas
                </p>
            </div>
        </body>
        </html>
        """

        # plain text fallback tetap ada
        plain_body = (
            f"Halo {dosen.nama},\n\n"
            f"Ada {jumlah_pending} permohonan pending.\n"
            "Mohon ditinjau.\n\nSalam,\nFTI-Service"
        )

        try:
            msg = Message(
                subject,
                recipients=[dosen.email],
                body=plain_body,   # fallback
                html=html_body     # versi berwarna
            )
            mail.send(msg)
        except Exception as e:
            print(f"[ERROR] gagal kirim email {dosen.email}: {e}")

    


def start_scheduler(app):
    """Inisialisasi APScheduler"""
    # Bungkus fungsi job agar memiliki app_context dari Flask
    def job_wrapper():
        with app.app_context():
            send_weekly_pending_notifications()

    # Jadwalkan job
    scheduler.add_job(
        func=job_wrapper,
        trigger='cron',
        day_of_week='*',  
        hour=9,             # Jam 09:00 WIB
        minute=00,
        timezone=pytz.timezone("Asia/Jakarta")
    )

    scheduler.start()
    
