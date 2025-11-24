# main.py
import os
from flask import Flask
from config.config import config_dict
from extensions import init_extensions

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config_dict[config_name])
    
    # Initialize extensions
    init_extensions(app)
    from app import models

    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.google_auth_controller import google_auth_bp
    from app.controllers.user_controller import user_bp
    from app.controllers.dosen_controller import dosen_bp
    from app.controllers.permohonan_controller import permohonan_bp
    from app.controllers.fakultas_controller import fakultas_bp

    # get list permohonan
    from app.controllers.jenis_permohonan_controller import jenis_permohonan_bp

    #get list file
    from app.controllers.file_controller import file_bp

    #after scan
    from app.controllers.verify_controller import verify_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(google_auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')

    #get permohohnan API
    app.register_blueprint(permohonan_bp, url_prefix='/api/permohonan')

    # get dosen untuk permohonan
    app.register_blueprint(dosen_bp,url_prefix='/api/dosen')

    # get program studi in fakultas
    app.register_blueprint(fakultas_bp,url_prefix='/api/fakultas')

    # get jenis_permohonan in table jenis permohonan 
    app.register_blueprint(jenis_permohonan_bp,url_prefix='/api/jenis-permohonan')

    # get file to dosen
    app.register_blueprint(file_bp, url_prefix='/api/files')

    # get data to qr 
    app.register_blueprint(verify_bp, url_prefix='/api/verify')

    # magasiswa get history
    from app.controllers.history_controller import history_bp
    app.register_blueprint(history_bp, url_prefix='/api/history')

    # admin get history
    from app.controllers.admin_controller import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Error handlers
    from utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=4000)


