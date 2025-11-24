# utils/notification_utils.py
from app.models.notification_model import Notification
from extensions import db

def create_notification(user_id, permohonan_id, title, message, notification_type):
    """Create new notification"""
    try:
        notification = Notification(
            user_id=user_id,
            permohonan_id=permohonan_id,
            title=title,
            message=message,
            type=notification_type
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception as e:
        db.session.rollback()
        raise e

def notify_permohonan_created(permohonan):
    """Send notification when permohonan is created"""
    create_notification(
        user_id=permohonan.id_dosen,
        permohonan_id=permohonan.id,
        title="Permohonan Baru",
        message=f"Ada permohonan baru dari {permohonan.mahasiswa.user.nama}: {permohonan.judul}",
        notification_type="new_request"
    )

def notify_permohonan_approved(permohonan):
    """Send notification when permohonan is approved"""
    create_notification(
        user_id=permohonan.id_mahasiswa,
        permohonan_id=permohonan.id,
        title="Permohonan Disetujui",
        message=f"Permohonan Anda '{permohonan.judul}' telah disetujui oleh {permohonan.dosen.nama_lengkap}",
        notification_type="approved"
    )

def notify_permohonan_rejected(permohonan):
    """Send notification when permohonan is rejected"""
    create_notification(
        user_id=permohonan.id_mahasiswa,
        permohonan_id=permohonan.id,
        title="Permohonan Ditolak",
        message=f"Permohonan Anda '{permohonan.judul}' ditolak. Alasan: {permohonan.komentar_penolakan}",
        notification_type="rejected"
    )

def notify_permohonan_signed(permohonan):
    """Send notification when permohonan is signed"""
    create_notification(
        user_id=permohonan.id_mahasiswa,
        permohonan_id=permohonan.id,
        title="Dokumen Ditandatangani",
        message=f"Dokumen permohonan '{permohonan.judul}' telah ditandatangani dan siap diunduh",
        notification_type="signed"
    )