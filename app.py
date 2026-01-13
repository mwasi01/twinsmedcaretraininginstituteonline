import os
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import docx
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy with app
db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')
    full_name = db.Column(db.String(100))
    course = db.Column(db.String(50), default='CNA')
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
    file_type = db.Column(db.String(20))
    course = db.Column(db.String(50), default='CNA')
    module = db.Column(db.String(100))
    due_date = db.Column(db.DateTime)
    max_score = db.Column(db.Integer, default=100)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.Column(db.Text)

class ExamSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answers = db.Column(db.Text)
    score = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='submitted')

class LibraryResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(200))
    resource_type = db.Column(db.String(20))
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
    """Create necessary upload folders"""
    try:
        folders = [
            'static/uploads/assignments',
            'static/uploads/library',
            'static/uploads/profile_pics',
            'instance'
        ]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        print("Created upload folders")
    except Exception as e:
        print(f"Warning: Could not create folders: {e}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
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
    
    submissions = ExamSubmission.query.filter_by(student_id=current_user.id).order_by(ExamSubmission.submitted_at.desc()).limit(3).all()
    
    return render_template('dashboard.html', 
                         assignments=assignments, 
                         resources=resources,
                         submissions=submissions,
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
        max_score = request.form.get('max_score', 100)
        file = request.files.get('file')
        
        if not title:
            flash('Title is required', 'danger')
            return redirect(url_for('upload_assignment'))
        
        assignment = Assignment(
            title=title,
            description=description,
            module=module,
            course=current_user.course,
            created_by=current_user.id,
            max_score=int(max_score)
        )
        
        if due_date:
            try:
                assignment.due_date = datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format. Use YYYY-MM-DD', 'danger')
                return redirect(url_for('upload_assignment'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], Config.ASSIGNMENTS_FOLDER, filename)
            file.save(filepath)
            assignment.filename = filename
            assignment.file_type = filename.rsplit('.', 1)[1].lower()
            
            if assignment.file_type == 'docx':
                questions = parse_docx_questions(filepath)
                if questions:
                    assignment.questions = json.dumps(questions)
            elif assignment.file_type == 'json':
                try:
                    with open(filepath, 'r') as f:
                        questions = json.load(f)
                        assignment.questions = json.dumps(questions)
                except json.JSONDecodeError:
                    flash('Invalid JSON file format', 'danger')
                    return redirect(url_for('upload_assignment'))
        
        db.session.add(assignment)
        db.session.commit()
        flash('Assignment uploaded successfully!', 'success')
        return redirect(url_for('assignments'))
    
    recent_assignments = Assignment.query.filter_by(created_by=current_user.id).order_by(Assignment.created_at.desc()).limit(3).all()
    
    return render_template('upload_assignment.html', recent_assignments=recent_assignments)

def parse_docx_questions(filepath):
    try:
        doc = docx.Document(filepath)
        questions = []
        current_question = None
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
                
            if text.lower().startswith(('q:', 'question:', 'q.', 'question.')):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    'question': text,
                    'options': [],
                    'correct_answer': '',
                    'question_type': 'multiple_choice',
                    'points': 1
                }
            elif text.lower().startswith(('a:', 'b:', 'c:', 'd:', 'a)', 'b)', 'c)', 'd)')):
                if current_question:
                    current_question['options'].append(text)
            elif text.lower().startswith(('answer:', 'correct:')):
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
    
    submissions = ExamSubmission.query.filter_by(student_id=current_user.id).all()
    submission_dict = {sub.assignment_id: sub for sub in submissions}
    
    return render_template('assignments.html', 
                         assignments=assignments_list,
                         submissions=submission_dict)

@app.route('/take_exam/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def take_exam(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if assignment.course != current_user.course:
        flash('This assignment is not available for your course', 'danger')
        return redirect(url_for('assignments'))
    
    existing_submission = ExamSubmission.query.filter_by(
        assignment_id=assignment_id,
        student_id=current_user.id
    ).first()
    
    if existing_submission:
        flash('You have already submitted this exam', 'warning')
        return redirect(url_for('assignments'))
    
    if request.method == 'POST':
        answers = request.form.to_dict()
        
        questions = json.loads(assignment.questions) if assignment.questions else []
        score = 0
        total_points = 0
        
        if questions:
            for i, q in enumerate(questions):
                points = q.get('points', 1)
                total_points += points
                user_answer = answers.get(f'question_{i}')
                
                if user_answer and user_answer == q.get('correct_answer'):
                    score += points
            
            final_score = (score / total_points * assignment.max_score) if total_points > 0 else 0
            status = 'graded'
        else:
            final_score = None
            status = 'submitted'
        
        submission = ExamSubmission(
            assignment_id=assignment_id,
            student_id=current_user.id,
            answers=json.dumps(answers),
            score=final_score,
            status=status
        )
        
        db.session.add(submission)
        db.session.commit()
        
        if final_score is not None:
            flash(f'Exam submitted! Your score: {final_score:.1f}%', 'success')
        else:
            flash('Exam submitted successfully! It will be graded manually.', 'success')
        
        return redirect(url_for('dashboard'))
    
    questions = json.loads(assignment.questions) if assignment.questions else []
    return render_template('take_exam.html', 
                         assignment=assignment, 
                         questions=questions)

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
    
    modules = db.session.query(LibraryResource.module).distinct().filter(LibraryResource.module.isnot(None)).all()
    
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
            filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], Config.LIBRARY_FOLDER, filename)
            file.save(filepath)
            
            resource = LibraryResource(
                title=title,
                description=description,
                resource_type=resource_type,
                module=module,
                course=current_user.course,
                filename=filename,
                uploaded_by=current_user.id
            )
            
            db.session.add(resource)
            db.session.commit()
            flash('Resource uploaded successfully!', 'success')
            return redirect(url_for('library'))
        else:
            flash('File type not allowed', 'danger')
            return redirect(url_for('upload_resource'))
    
    recent_resources = LibraryResource.query.filter_by(uploaded_by=current_user.id).order_by(LibraryResource.uploaded_at.desc()).limit(3).all()
    
    return render_template('upload_resource.html', recent_resources=recent_resources)

@app.route('/download/<resource_type>/<filename>')
@login_required
def download_file(resource_type, filename):
    if resource_type == 'assignment':
        folder = Config.ASSIGNMENTS_FOLDER
        assignment = Assignment.query.filter_by(filename=filename).first()
        if assignment and assignment.course != current_user.course:
            flash('You do not have access to this file', 'danger')
            return redirect(url_for('assignments'))
    elif resource_type == 'library':
        folder = Config.LIBRARY_FOLDER
        resource = LibraryResource.query.filter_by(filename=filename).first()
        if resource and resource.course != current_user.course:
            flash('You do not have access to this file', 'danger')
            return redirect(url_for('library'))
    else:
        flash('Invalid resource type', 'danger')
        return redirect(url_for('dashboard'))
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    
    if not os.path.exists(filepath):
        flash('File not found', 'danger')
        return redirect(url_for('dashboard'))
    
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
    submissions = ExamSubmission.query.all()
    
    total_users = len(users)
    total_assignments = len(assignments)
    total_resources = len(resources)
    total_submissions = len(submissions)
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         assignments=assignments, 
                         resources=resources,
                         submissions=submissions,
                         total_users=total_users,
                         total_assignments=total_assignments,
                         total_resources=total_resources,
                         total_submissions=total_submissions)

@app.route('/admin/delete_user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/delete_assignment/<int:assignment_id>', methods=['DELETE'])
@login_required
def delete_assignment(assignment_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if assignment.filename:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], Config.ASSIGNMENTS_FOLDER, assignment.filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
    
    db.session.delete(assignment)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/delete_resource/<int:resource_id>', methods=['DELETE'])
@login_required
def delete_resource(resource_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    resource = LibraryResource.query.get_or_404(resource_id)
    
    if resource.filename:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], Config.LIBRARY_FOLDER, resource.filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
    
    db.session.delete(resource)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/update_user/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.role = request.form.get('role', user.role)
    user.course = request.form.get('course', user.course)
    user.full_name = request.form.get('full_name', user.full_name)
    user.email = request.form.get('email', user.email)
    
    new_password = request.form.get('new_password')
    if new_password and len(new_password) >= 6:
        user.set_password(new_password)
    
    db.session.commit()
    flash('User updated successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.full_name = request.form.get('full_name')
    current_user.email = request.form.get('email')
    current_user.course = request.form.get('course')
    
    current_password = request.form.get('current_password')
    if current_password and not current_user.check_password(current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('profile'))
    
    new_password = request.form.get('new_password')
    if new_password and len(new_password) >= 6:
        current_user.set_password(new_password)
    
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    role = request.form.get('role', 'student')
    course = request.form.get('course', 'CNA')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already registered', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        role=role,
        course=course
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    flash('User created successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/profile')
@login_required
def profile():
    submissions = ExamSubmission.query.filter_by(student_id=current_user.id).order_by(ExamSubmission.submitted_at.desc()).all()
    
    assignments = {a.id: a for a in Assignment.query.filter_by(course=current_user.course).all()}
    
    return render_template('profile.html', 
                         user=current_user, 
                         submissions=submissions,
                         assignments=assignments)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/clear_cache', methods=['POST'])
@login_required
def clear_cache():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({'success': True})

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

@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

# Initialize database and create upload folders
def initialize_database():
    with app.app_context():
        try:
            # Create upload folders first
            create_upload_folders()
            
            # Create tables
            db.create_all()
            print("Database tables created")
            
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
                print("Created admin user: admin / admin123")
            
            # Create default instructor if not exists
            if not User.query.filter_by(username='instructor').first():
                instructor = User(
                    username='instructor',
                    email='instructor@twinsmedcare.edu',
                    full_name='Course Instructor',
                    role='instructor',
                    course='CNA'
                )
                instructor.set_password('instructor123')
                db.session.add(instructor)
                print("Created instructor user: instructor / instructor123")
            
            db.session.commit()
            print("Database initialized successfully")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            # Don't crash if database initialization fails
            # The app will still run and try to reconnect

# Run initialization
try:
    initialize_database()
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")
    print("App will continue running...")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
