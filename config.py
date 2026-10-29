import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-student-mgmt-2026-production-ready')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'student_system.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB total request limit
    
    ALLOWED_REPORT_EXTENSIONS = {'pdf'}
    ALLOWED_CODE_EXTENSIONS = {'zip'}
    ALLOWED_ATTACHMENT_EXTENSIONS = {'pdf', 'zip', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}
    
    MAX_REPORT_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_CODE_SIZE = 25 * 1024 * 1024    # 25 MB
    MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB
    
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'instance', 'test_uploads')
