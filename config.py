import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings - Increased for large educational files
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB max file size
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'json',
        'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv',  # Video formats
        'mp3', 'wav', 'm4a',  # Audio formats
        'ppt', 'pptx', 'xls', 'xlsx',  # Office formats
        'zip', 'rar', '7z'  # Archive formats
    }
    
    # Library paths
    ASSIGNMENTS_FOLDER = 'assignments'
    LIBRARY_FOLDER = 'library'
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Temporary upload folder
    TEMP_UPLOAD_FOLDER = 'static/temp_uploads'
