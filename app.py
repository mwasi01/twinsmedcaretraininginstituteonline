import os
import json
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import docx
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')  # student, instructor, admin
    full_name = db.Column(db.String(100))
    course = db.Column(db.String(50), default='CNA')  # Certified Nursing Assistant
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(200))
    file_type = db.Column(db.String(20))  # json, docx, pdf
    course = db.Column(db.String(50), default='CNA')
    module = db.Column(db.String(100))
    due_date = db.Column(db.DateTime)
    max_score = db.Column(db.Integer, default=100)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.Column(db.Text)  # JSON string for quiz questions

class ExamSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answers = db.Column(db.Text)  # JSON string
    score = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='submitted')  # submitted, graded

class LibraryResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(200))
    resource_type = db.Column(db.String(20))  # video, notes, past_paper
    course = db.Column(db.String(50), default='CNA')
    module = db.Column(db.String(100))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def create_upload_folders():
    folders = [
        os.path.join(app.config['UPLOAD_FOLDER'], Config.ASSIGNMENTS_FOLDER),
        os.path.join(app.config['UPLOAD_FOLDER'], Config.LIBRARY_FOLDER),
        'static/uploads/profile_pics',
        Config.TEMP_UPLOAD_FOLDER
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        course = request.form.get('course', 'CNA')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            course=course,
            role='student'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    assignments = Assignment.query.filter_by(course=current_user.course).order_by(Assignment.created_at.desc()).limit(5).all()
    resources = LibraryResource.query.filter_by(course=current_user.course).order_by(LibraryResource.uploaded_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         assignments=assignments, 
                         resources=resources,
                         user=current_user)

@app.route('/upload_assignment', methods=['GET', 'POST'])
@login_required
def upload_assignment():
    if current_user.role not in ['instructor', 'admin']:
        flash('You do not have permission to upload assignments', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        module = request.form.get('module')
        due_date = request.form.get('due_date')
        file = request.files.get('file')
        
        if not title:
            flash('Title is required', 'danger')
            return redirect(url_for('upload_assignment'))
        
        assignment = Assignment(
            title=title,
            description=description,
            module=module,
            course='CNA',
            created_by=current_user.id
        )
        
        if due_date:
            assignment.due_date = datetime.strptime(due_date, '%Y-%m-%d')
        
        if file and allowed_file(file.filename):
            try:
                # Save the file
                timestamp = datetime.now().timestamp()
                original_filename = secure_filename(file.filename)
                filename = f"{timestamp}_{original_filename}"
                folder = os.path.join(app.config['UPLOAD_FOLDER'], Config.ASSIGNMENTS_FOLDER)
                filepath = os.path.join(folder, filename)
                file.save(filepath)
                
                assignment.filename = filename
                assignment.file_type = filename.rsplit('.', 1)[1].lower()
                
                # Parse file for questions
                if assignment.file_type == 'docx':
                    questions = parse_docx_questions(filepath)
                    assignment.questions = json.dumps(questions)
                elif assignment.file_type == 'json':
                    with open(filepath, 'r') as f:
                        questions = json.load(f)
                        assignment.questions = json.dumps(questions)
                
                # Get file size
                file_size = os.path.getsize(filepath)
                size_mb = file_size / (1024 * 1024)
                
                db.session.add(assignment)
                db.session.commit()
                
                flash(f'Assignment uploaded successfully! ({size_mb:.2f} MB)', 'success')
                return redirect(url_for('assignments'))
                
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'danger')
                return redirect(url_for('upload_assignment'))
        else:
            flash('File type not allowed', 'danger')
            return redirect(url_for('upload_assignment'))
    
    return render_template('upload_assignment.html')

def parse_docx_questions(filepath):
    """Parse docx file to extract questions"""
    try:
        doc = docx.Document(filepath)
        questions = []
        current_question = None
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
                
            if text.startswith(('Q:', 'Question:', 'Q.', 'Question.', 'Q)', 'Question)')) or \
               (text[0].isdigit() and text[1] in ['.', ')', ':']):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    'question': text,
                    'options': [],
                    'correct_answer': '',
                    'question_type': 'multiple_choice'
                }
            elif text.startswith(('A:', 'B:', 'C:', 'D:', 'a)', 'b)', 'c)', 'd)', 'a.', 'b.', 'c.', 'd.')):
                if current_question:
                    current_question['options'].append(text)
            elif text.startswith(('Answer:', 'Correct:', 'Correct Answer:')):
                if current_question:
                    parts = text.split(':', 1)
                    if len(parts) > 1:
                        current_question['correct_answer'] = parts[1].strip()
        
        if current_question:
            questions.append(current_question)
        
        return questions
    except Exception as e:
        print(f"Error parsing DOCX: {e}")
        return []

@app.route('/assignments')
@login_required
def assignments():
    assignments_list = Assignment.query.filter_by(course=current_user.course).order_by(Assignment.created_at.desc()).all()
    return render_template('assignments.html', assignments=assignments_list)

@app.route('/take_exam/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def take_exam(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if request.method == 'POST':
        answers = request.form.to_dict()
        
        # Calculate score
        questions = json.loads(assignment.questions) if assignment.questions else []
        score = 0
        total = len(questions)
        
        for i, q in enumerate(questions):
            user_answer = answers.get(f'question_{i}')
            if user_answer and user_answer == q.get('correct_answer'):
                score += 1
        
        final_score = (score / total * 100) if total > 0 else 0
        
        submission = ExamSubmission(
            assignment_id=assignment_id,
            student_id=current_user.id,
            answers=json.dumps(answers),
            score=final_score
        )
        
        db.session.add(submission)
        db.session.commit()
        
        flash(f'Exam submitted! Your score: {final_score:.1f}%', 'success')
        return redirect(url_for('dashboard'))
    
    questions = json.loads(assignment.questions) if assignment.questions else []
    return render_template('take_exam.html', assignment=assignment, questions=questions)

@app.route('/library')
@login_required
def library():
    resource_type = request.args.get('type', 'all')
    module = request.args.get('module', 'all')
    
    query = LibraryResource.query.filter_by(course=current_user.course)
    
    if resource_type != 'all':
        query = query.filter_by(resource_type=resource_type)
    if module != 'all':
        query = query.filter_by(module=module)
    
    resources = query.order_by(LibraryResource.uploaded_at.desc()).all()
    
    # Get unique modules for filter
    modules = db.session.query(LibraryResource.module).distinct().all()
    
    return render_template('library.html', 
                         resources=resources, 
                         modules=[m[0] for m in modules if m[0]],
                         current_type=resource_type,
                         current_module=module)

@app.route('/upload_resource', methods=['GET', 'POST'])
@login_required
def upload_resource():
    if current_user.role not in ['instructor', 'admin']:
        flash('You do not have permission to upload resources', 'danger')
        return redirect(url_for('library'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        resource_type = request.form.get('type')
        module = request.form.get('module')
        file = request.files.get('file')
        
        if not title or not file:
            flash('Title and file are required', 'danger')
            return redirect(url_for('upload_resource'))
        
        if allowed_file(file.filename):
            try:
                # Save the file
                timestamp = datetime.now().timestamp()
                original_filename = secure_filename(file.filename)
                filename = f"{timestamp}_{original_filename}"
                folder = os.path.join(app.config['UPLOAD_FOLDER'], Config.LIBRARY_FOLDER)
                filepath = os.path.join(folder, filename)
                file.save(filepath)
                
                resource = LibraryResource(
                    title=title,
                    description=description,
                    resource_type=resource_type,
                    module=module,
                    course='CNA',
                    filename=filename,
                    uploaded_by=current_user.id
                )
                
                # Get file size
                file_size = os.path.getsize(filepath)
                size_mb = file_size / (1024 * 1024)
                
                db.session.add(resource)
                db.session.commit()
                
                flash(f'Resource uploaded successfully! ({size_mb:.2f} MB)', 'success')
                return redirect(url_for('library'))
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'danger')
                return redirect(url_for('upload_resource'))
        else:
            flash('File type not allowed', 'danger')
            return redirect(url_for('upload_resource'))
    
    return render_template('upload_resource.html')

@app.route('/download/<resource_type>/<filename>')
@login_required
def download_file(resource_type, filename):
    if resource_type == 'assignment':
        folder = Config.ASSIGNMENTS_FOLDER
    else:  # library resource
        folder = Config.LIBRARY_FOLDER
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    
    # Update view count for library resources
    if resource_type == 'library':
        resource = LibraryResource.query.filter_by(filename=filename).first()
        if resource:
            resource.views += 1
            db.session.commit()
    
    return send_file(filepath, as_attachment=True)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    assignments = Assignment.query.all()
    resources = LibraryResource.query.all()
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         assignments=assignments, 
                         resources=resources)

@app.route('/profile')
@login_required
def profile():
    submissions = ExamSubmission.query.filter_by(student_id=current_user.id).all()
    return render_template('profile.html', user=current_user, submissions=submissions)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# CNA Course Modules
CNA_MODULES = [
    'Basic Nursing Skills',
    'Personal Care Skills',
    'Mental Health and Social Service Needs',
    'Care of Cognitively Impaired Residents',
    'Basic Restorative Services',
    'Resident Rights',
    'Safety and Emergency Procedures',
    'Infection Control',
    'Anatomy and Physiology',
    'Medical Terminology'
]

@app.context_processor
def inject_modules():
    return dict(cna_modules=CNA_MODULES)

# Initialize database
with app.app_context():
    db.create_all()
    create_upload_folders()
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@twinsmedcare.edu',
            full_name='System Administrator',
            role='admin',
            course='CNA'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
