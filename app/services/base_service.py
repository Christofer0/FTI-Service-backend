# services/base_service.py
class BaseService:
    """Base service class"""
    
    def __init__(self, repository):
        self.repository = repository

