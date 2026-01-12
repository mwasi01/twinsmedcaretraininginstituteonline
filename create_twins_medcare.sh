#!/bin/bash

# twins-medcare-platform file structure creator
# Creates directory structure and empty files for the platform

# Base directory
BASE_DIR="twins-medcare-platform"

echo "Creating Twins-MedCare Platform directory structure..."

# Create base directory
mkdir -p "$BASE_DIR"

# Create root level files
touch "$BASE_DIR/app.py"
touch "$BASE_DIR/requirements.txt"
touch "$BASE_DIR/render.yaml"
touch "$BASE_DIR/config.py"

# Create static directory structure
mkdir -p "$BASE_DIR/static/css"
mkdir -p "$BASE_DIR/static/js"
mkdir -p "$BASE_DIR/static/uploads/assignments"
mkdir -p "$BASE_DIR/static/uploads/library"
mkdir -p "$BASE_DIR/static/uploads/profile_pics"

# Create static files
touch "$BASE_DIR/static/css/style.css"
touch "$BASE_DIR/static/js/main.js"

# Create templates directory and files
mkdir -p "$BASE_DIR/templates"

templates=(
    "layout.html"
    "index.html"
    "login.html"
    "register.html"
    "dashboard.html"
    "upload_assignment.html"
    "assignments.html"
    "take_exam.html"
    "library.html"
    "admin_dashboard.html"
    "profile.html"
)

for template in "${templates[@]}"; do
    touch "$BASE_DIR/templates/$template"
done

# Create instance directory and database file
mkdir -p "$BASE_DIR/instance"
touch "$BASE_DIR/instance/database.db"

# Set execute permission for Python files
chmod +x "$BASE_DIR/app.py"

# Create a basic requirements.txt with common dependencies
cat > "$BASE_DIR/requirements.txt" << EOF
Flask>=2.3.0
Flask-SQLAlchemy>=3.0.0
Flask-Login>=0.6.0
Flask-WTF>=1.1.0
python-dotenv>=1.0.0
Werkzeug>=2.3.0
EOF

# Create a basic render.yaml for deployment
cat > "$BASE_DIR/render.yaml" << EOF
services:
  - type: web
    name: twins-medcare-platform
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
EOF

# Create a basic config.py
cat > "$BASE_DIR/config.py" << EOF
import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    ASSIGNMENT_UPLOAD_FOLDER = 'static/uploads/assignments'
    LIBRARY_UPLOAD_FOLDER = 'static/uploads/library'
    PROFILE_PICS_FOLDER = 'static/uploads/profile_pics'
    
    # Allowed file extensions
    ALLOWED_ASSIGNMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'zip'}
    ALLOWED_LIBRARY_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'}
    ALLOWED_PROFILE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Security
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
EOF

# Create a basic app.py skeleton
cat > "$BASE_DIR/app.py" << 'EOF'
#!/usr/bin/env python3

"""
Twins-MedCare Platform
A comprehensive platform for managing medical care and assignments
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
import os
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import models (to be created)
# from models import User, Assignment, Exam, LibraryItem, Profile

# Create upload directories if they don't exist
os.makedirs(app.config['ASSIGNMENT_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['LIBRARY_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_PICS_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        # Handle login logic here
        pass
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        # Handle registration logic here
        pass
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return render_template('dashboard.html')

@app.route('/upload_assignment', methods=['GET', 'POST'])
@login_required
def upload_assignment():
    """Upload assignment page"""
    return render_template('upload_assignment.html')

@app.route('/assignments')
@login_required
def assignments():
    """View assignments"""
    return render_template('assignments.html')

@app.route('/take_exam')
@login_required
def take_exam():
    """Take exam page"""
    return render_template('take_exam.html')

@app.route('/library')
@login_required
def library():
    """Library/resources page"""
    return render_template('library.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin_dashboard.html')

@app.route('/profile')
@login_required
def profile():
    """User profile"""
    return render_template('profile.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
EOF

# Create a basic CSS file
cat > "$BASE_DIR/static/css/style.css" << 'EOF'
/* Twins-MedCare Platform Main Stylesheet */

:root {
    --primary-color: #2563eb;
    --secondary-color: #7c3aed;
    --accent-color: #10b981;
    --danger-color: #ef4444;
    --warning-color: #f59e0b;
    --light-color: #f8fafc;
    --dark-color: #1e293b;
    --gray-color: #64748b;
    --border-color: #e2e8f0;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: var(--dark-color);
    background-color: var(--light-color);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Navigation */
.navbar {
    background-color: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    padding: 1rem 0;
}

.navbar-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
    text-decoration: none;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.375rem;
    font-weight: 500;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary {
    background-color: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background-color: #1d4ed8;
}

.btn-secondary {
    background-color: var(--secondary-color);
    color: white;
}

/* Cards */
.card {
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* Forms */
.form-group {
    margin-bottom: 1rem;
}

.form-control {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    font-size: 1rem;
}

.form-control:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Dashboard */
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-top: 2rem;
}

/* Responsive */
@media (max-width: 768px) {
    .container {
        padding: 0 15px;
    }
    
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
}

/* Utility classes */
.text-center { text-align: center; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 1rem; }
.mt-4 { margin-top: 1.5rem; }
.mt-5 { margin-top: 2rem; }
EOF

# Create a basic JavaScript file
cat > "$BASE_DIR/static/js/main.js" << 'EOF'
/**
 * Twins-MedCare Platform Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize file upload previews
    initFileUploadPreviews();
});

/**
 * Initialize Bootstrap-like tooltips
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-toggle="tooltip"]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltipText = this.getAttribute('title');
            if (tooltipText) {
                const tooltip = document.createElement('div');
                tooltip.className = 'custom-tooltip';
                tooltip.textContent = tooltipText;
                document.body.appendChild(tooltip);
                
                const rect = this.getBoundingClientRect();
                tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
                tooltip.style.left = (rect.left + (rect.width - tooltip.offsetWidth) / 2) + 'px';
                
                this._tooltip = tooltip;
                this.removeAttribute('title');
            }
        });
        
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this.setAttribute('title', this._tooltip.textContent);
            }
        });
    });
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
}

/**
 * Initialize file upload previews
 */
function initFileUploadPreviews() {
    const fileInputs = document.querySelectorAll('.file-upload');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const previewContainer = document.getElementById(this.dataset.previewContainer);
            if (previewContainer) {
                previewContainer.innerHTML = '';
                
                Array.from(this.files).forEach(file => {
                    const preview = document.createElement('div');
                    preview.className = 'file-preview';
                    preview.innerHTML = `
                        <span class="file-name">${file.name}</span>
                        <span class="file-size">(${formatFileSize(file.size)})</span>
                    `;
                    previewContainer.appendChild(preview);
                });
            }
        });
    });
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Show notification/toast message
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

/**
 * Confirm dialog helper
 */
function confirmAction(message) {
    return new Promise((resolve) => {
        if (confirm(message)) {
            resolve(true);
        } else {
            resolve(false);
        }
    });
}
EOF

# Create a basic HTML layout template
cat > "$BASE_DIR/templates/layout.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Twins-MedCare Platform{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <a href="{{ url_for('index') }}" class="navbar-brand">
                <i class="fas fa-stethoscope"></i> Twins-MedCare
            </a>
            <div class="navbar-menu">
                {% if current_user.is_authenticated %}
                    <a href="{{ url_for('dashboard') }}">Dashboard</a>
                    <a href="{{ url_for('assignments') }}">Assignments</a>
                    <a href="{{ url_for('library') }}">Library</a>
                    <a href="{{ url_for('profile') }}">Profile</a>
                    {% if current_user.is_admin %}
                        <a href="{{ url_for('admin_dashboard') }}">Admin</a>
                    {% endif %}
                    <a href="{{ url_for('logout') }}">Logout</a>
                {% else %}
                    <a href="{{ url_for('login') }}">Login</a>
                    <a href="{{ url_for('register') }}">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <footer>
        <div class="container">
            <p>&copy; {{ now.year }} Twins-MedCare Platform. All rights reserved.</p>
        </div>
    </footer>

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
{% set now = now or datetime.now() %}
EOF

# Create basic HTML templates
create_basic_html() {
    local file="$1"
    local title="$2"
    
    cat > "$BASE_DIR/templates/$file" << EOF
{% extends "layout.html" %}

{% block title %}$title - Twins-MedCare Platform{% endblock %}

{% block content %}
<div class="page-header">
    <h1>$title</h1>
</div>

<div class="page-content">
    <!-- Page content will go here -->
    <div class="card">
        <p>This is the $title page. Content will be added here.</p>
    </div>
</div>
{% endblock %}
EOF
}

# Create all HTML templates
create_basic_html "index.html" "Home"
create_basic_html "login.html" "Login"
create_basic_html "register.html" "Register"
create_basic_html "dashboard.html" "Dashboard"
create_basic_html "upload_assignment.html" "Upload Assignment"
create_basic_html "assignments.html" "Assignments"
create_basic_html "take_exam.html" "Take Exam"
create_basic_html "library.html" "Library"
create_basic_html "admin_dashboard.html" "Admin Dashboard"
create_basic_html "profile.html" "Profile"

echo "✅ Twins-MedCare Platform structure created successfully!"
echo ""
echo "📁 Directory structure created at: $BASE_DIR"
echo ""
echo "📋 Project structure:"
find "$BASE_DIR" -type f | sort | sed 's|^|    |'
echo ""
echo "🚀 To get started:"
echo "   cd $BASE_DIR"
echo "   pip install -r requirements.txt"
echo "   python app.py"
echo ""
echo "🌐 Then visit: http://localhost:5000"
