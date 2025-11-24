# repositories/notification_repository.py
from typing import List
from app.models.notification_model import Notification
from .base_repository import BaseRepository

class NotificationRepository(BaseRepository):
    """Repository for Notification operations"""
    
    def __init__(self):
        super().__init__(Notification)
    
    def get_by_user(self, user_id: str, unread_only: bool = False) -> List[Notification]:
        """Get notifications by user"""
        query = self.session.query(Notification).filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc()).all()
    
    def mark_as_read(self, notification_id: int, user_id: str) -> bool:
        """Mark notification as read"""
        notification = self.session.query(Notification)\
            .filter_by(id=notification_id, user_id=user_id)\
            .first()
        
        if notification and not notification.is_read:
            notification.is_read = True
            self.session.commit()
            return True
        return False
    
    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all user notifications as read"""
        updated = self.session.query(Notification)\
            .filter_by(user_id=user_id, is_read=False)\
            .update({'is_read': True})
        self.session.commit()
        return updated
    
    def get_unread_count(self, user_id: str) -> int:
        """Get unread notifications count"""
        return self.session.query(Notification)\
            .filter_by(user_id=user_id, is_read=False)\
            .count()