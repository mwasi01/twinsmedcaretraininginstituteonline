import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Always use DATABASE_URL from environment in production
    if os.environ.get('DATABASE_URL'):
        # Handle both postgres:// and postgresql://
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # For local development, use SQLite in instance folder
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'database.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'json', 'mp4', 'avi', 'mov', 'wmv', 'pptx', 'zip'}
    
    # Library paths
    ASSIGNMENTS_FOLDER = 'assignments'
    LIBRARY_FOLDER = 'library'
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
