#!/bin/bash

# Clean up and fix the directory structure

echo "Fixing directory structure..."

# Check if we're in the right location
if [ -d "twins-medcare-platform" ] && [ -d "twins-medcare-platform/twins-medcare-platform" ]; then
    echo "Found nested structure. Fixing..."
    
    # Move everything up one level
    mv twins-medcare-platform/twins-medcare-platform/* twins-medcare-platform/
    rm -rf twins-medcare-platform/twins-medcare-platform
    
    echo "✅ Structure fixed!"
    echo ""
    echo "📁 Correct structure at: twins-medcare-platform"
    echo ""
    echo "📋 Files in the project:"
    find twins-medcare-platform -type f | sort | sed 's|^|    |'
else
    echo "No nested structure found or already fixed."
fi

# Create a fixed app.py with better error handling
cat > twins-medcare-platform/app.py << 'APPEOF'
#!/usr/bin/env python3

"""
Twins-MedCare Platform
A comprehensive platform for managing medical care and assignments
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create instance directory if it doesn't exist
os.makedirs('instance', exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Create upload directories
os.makedirs('static/uploads/assignments', exist_ok=True)
os.makedirs('static/uploads/library', exist_ok=True)
os.makedirs('static/uploads/profile_pics', exist_ok=True)

# Simple User model for now
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        # Handle login logic here
        flash('Login functionality not yet implemented', 'info')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        # Handle registration logic here
        flash('Registration functionality not yet implemented', 'info')
        return redirect(url_for('index'))
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

@app.route('/setup')
def setup():
    """Setup route to initialize database"""
    try:
        db.create_all()
        
        # Create a default admin user if none exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', email='admin@example.com', is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            flash('Database initialized with admin user', 'success')
        else:
            flash('Database already initialized', 'info')
            
    except Exception as e:
        flash(f'Error initializing database: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

# Mock login/logout for development
@app.route('/dev_login')
def dev_login():
    """Development login - REMOVE IN PRODUCTION"""
    user = User.query.filter_by(username='admin').first()
    if not user:
        user = User(username='admin', email='admin@example.com', is_admin=True)
        db.session.add(user)
        db.session.commit()
    login_user(user)
    flash('Logged in as admin (dev mode)', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Context processor to add current year to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

if __name__ == '__main__':
    print("Starting Twins-MedCare Platform...")
    print("Visit http://localhost:5000")
    print("For development login, visit: http://localhost:5000/dev_login")
    app.run(debug=True, host='0.0.0.0', port=5000)
APPEOF

echo ""
echo "✅ Fixed app.py created with better error handling"
echo ""
echo "🚀 To get started:"
echo "   cd twins-medcare-platform"
echo "   python app.py"
echo ""
echo "🔧 First, initialize the database:"
echo "   Visit: http://localhost:5000/setup"
echo ""
echo "👤 For development login:"
echo "   Visit: http://localhost:5000/dev_login"
