# services/notification_service.py
from .base_service import BaseService
from app.repositories.notification_repository import NotificationRepository

class NotificationService(BaseService):
    """Service for notification operations"""
    
    def __init__(self):
        self.notification_repo = NotificationRepository()
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False):
        """Get user notifications"""
        return self.notification_repo.get_by_user(user_id, unread_only)
    
    def mark_notification_read(self, notification_id: int, user_id: str):
        """Mark notification as read"""
        return self.notification_repo.mark_as_read(notification_id, user_id)
    
    def mark_all_notifications_read(self, user_id: str):
        """Mark all notifications as read"""
        return self.notification_repo.mark_all_as_read(user_id)
    
    def get_unread_count(self, user_id: str):
        """Get unread notifications count"""
        return self.notification_repo.get_unread_count(user_id)