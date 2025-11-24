# repositories/base_repository.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Query
from sqlalchemy.exc import SQLAlchemyError
from extensions import db

class BaseRepository:
    """Base repository with common database operations"""
    
    def __init__(self, model):
        self.model = model
        self.session = db.session
    
    def create(self, **kwargs) -> Optional[Any]:
        """Create new record"""
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            self.session.commit()
            return instance
        except SQLAlchemyError:
            self.session.rollback()
            raise
    
    def get_by_id(self, id: Any) -> Optional[Any]:
        """Get record by ID"""
        return self.session.query(self.model).get(id)
    
    def get_all(self, **filters) -> List[Any]:
        """Get all records with optional filters"""
        query = self.session.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.all()
    
    def get_paginated(self, page: int = 1, per_page: int = 10, **filters):
        """Get paginated records"""
        query = self.session.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    def update(self, id: Any, **kwargs) -> Optional[Any]:
        """Update record by ID"""
        try:
            instance = self.get_by_id(id)
            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                self.session.commit()
                return instance
            return None
        except SQLAlchemyError:
            self.session.rollback()
            raise
    
    def delete(self, id: Any) -> bool:
        """Delete record by ID"""
        try:
            instance = self.get_by_id(id)
            if instance:
                self.session.delete(instance)
                self.session.commit()
                return True
            return False
        except SQLAlchemyError:
            self.session.rollback()
            raise
    
    def count(self, **filters) -> int:
        """Count records with filters"""
        query = self.session.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.count()