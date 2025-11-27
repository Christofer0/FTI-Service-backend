# config.py
import os, pytz
from datetime import timedelta
from decouple import config

class Config:
    # Basic Flask config
    SECRET_KEY = config('SECRET_KEY', default='dev-secret-key')
    
    # Database config
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default='sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT config
    JWT_SECRET_KEY = config('JWT_SECRET_KEY', default='jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(config('JWT_ACCESS_TOKEN_EXPIRES', default=3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(config('JWT_REFRESH_TOKEN_EXPIRES', default=2592000)))
    JWT_ALGORITHM = 'HS256'

    # Google OAuth config
    GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')
    GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    
    # Allowed email domains (untuk pengecekan email institusi)
    # Sesuaikan dengan domain email kampus Anda
    ALLOWED_EMAIL_DOMAINS = config('ALLOWED_EMAIL_DOMAINS', default='uksw.edu').split(',')
    
    # File upload config
    UPLOAD_FOLDER = config('UPLOAD_FOLDER', default='uploads')
    QR_CODE_FOLDER = config('QR_CODE_FOLDER', default='uploads/qr_codes')
    UPLOAD_SIGNED = config('UPLOAD_SIGNED', default='storage/signed')
    DOCUMENT_PERMOHONAN_TTD_PATH = config('DOCUMENT_PERMOHONAN_TTD_PATH', default='storage/signed/permohonan_ttd')
    MAX_CONTENT_LENGTH = int(config('MAX_CONTENT_LENGTH', default=16777216))  # 16MB
    ALLOWED_EXTENSIONS = set(config('ALLOWED_EXTENSIONS', default='pdf,doc,docx,jpg,jpeg,png').split(','))
    FRONTEND_URL = config('FRONTEND_URL', default='https://fti-service.netlify.app')

    # Admin Email untuk maintenance report
    ADMIN_EMAIL = config('ADMIN_EMAIL', default='brilliancw06@gmail.com')
    
    # APScheduler Configuration
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = pytz.timezone('Asia/Jakarta')

    # Email / SMTP config
    MAIL_SERVER = config('MAIL_SERVER', default='smtp.gmail.com')
    MAIL_PORT = config('MAIL_PORT', default=587, cast=int)
    MAIL_USE_TLS = config('MAIL_USE_TLS', default=True, cast=bool)
    MAIL_USE_SSL = config('MAIL_USE_SSL', default=False, cast=bool)
    MAIL_USERNAME = config('MAIL_USERNAME', default=None)
    MAIL_PASSWORD = config('MAIL_PASSWORD', default=None)
    MAIL_DEFAULT_SENDER = config('MAIL_DEFAULT_SENDER', default=config('MAIL_USERNAME', default=None))

    BATCH_CHUNK_SIZE = 10          # Process 10 permohonan at a time
    EMAIL_BATCH_SIZE = 20          # Send 20 emails per batch
    MAX_EMAIL_WORKERS = 5          # Max 5 concurrent email threads
    MAX_BATCH_PERMOHONAN = 100     # Hard limit untuk safety
    
    # Database Optimization
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,              # Reduced dari default 10
        'pool_recycle': 3600,        # Recycle connections after 1 hour
        'pool_pre_ping': True,       # Test connections before use
        'max_overflow': 2            # Reduced dari default 10
    }
    

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# class TestingConfig(Config):
#     TESTING = True
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    # 'testing': TestingConfig
}