from datetime import datetime, timezone
import os
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    register_no = db.Column(db.String(50), nullable=True, index=True)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student', 'faculty', 'admin'
    department = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)  # 1, 2, 3, 4
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    assignments_created = db.relationship('Assignment', backref='faculty', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='student', lazy=True, cascade='all, delete-orphan')
    evaluations_given = db.relationship('Evaluation', backref='faculty', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan', order_by='desc(Notification.created_at)')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def is_student(self):
        return self.role == 'student'
        
    @property
    def is_faculty(self):
        return self.role == 'faculty'
        
    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    max_marks = db.Column(db.Float, default=100.0, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    allow_late = db.Column(db.Boolean, default=True, nullable=False)
    attachment_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    submissions = db.relationship('Submission', backref='assignment', lazy=True, cascade='all, delete-orphan')

    @property
    def is_past_deadline(self):
        now = datetime.now(timezone.utc)
        # handle naive vs aware
        dl = self.deadline
        if dl.tzinfo is None:
            dl = dl.replace(tzinfo=timezone.utc)
        return now > dl

    @property
    def attachment_filename(self):
        if self.attachment_path:
            return os.path.basename(self.attachment_path)
        return None

    def __repr__(self):
        return f'<Assignment {self.title}>'


class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    report_path = db.Column(db.String(255), nullable=False)
    code_path = db.Column(db.String(255), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_late = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(30), default='Submitted', nullable=False)  
    # 'Submitted', 'Under Review', 'Approved', 'Needs Revision', 'Rejected'
    is_latest = db.Column(db.Boolean, default=True, nullable=False)
    
    evaluation = db.relationship('Evaluation', backref='submission', uselist=False, cascade='all, delete-orphan')

    @property
    def report_filename(self):
        return os.path.basename(self.report_path) if self.report_path else None

    @property
    def code_filename(self):
        return os.path.basename(self.code_path) if self.code_path else None

    def __repr__(self):
        return f'<Submission {self.id} Assg:{self.assignment_id} v{self.version}>'


class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id', ondelete='CASCADE'), unique=True, nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    evaluated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<Evaluation {self.id} Marks:{self.marks}>'


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<Notification {self.id} for {self.user_id}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<ActivityLog {self.action} by User {self.user_id}>'
