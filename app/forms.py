from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SelectField, IntegerField, FloatField, TextAreaField, DateTimeLocalField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, ValidationError
from app.models import User

DEPARTMENTS = [
    ('Computer Science', 'Computer Science'),
    ('Information Technology', 'Information Technology'),
    ('Electronics & Communication', 'Electronics & Communication'),
    ('Electrical & Electronics', 'Electrical & Electronics'),
    ('Mechanical Engineering', 'Mechanical Engineering')
]

YEARS = [
    (1, '1st Year'),
    (2, '2nd Year'),
    (3, '3rd Year'),
    (4, '4th Year')
]

ROLES = [
    ('student', 'Student'),
    ('faculty', 'Faculty'),
    ('admin', 'Admin')
]

STATUS_CHOICES = [
    ('Approved', 'Approved'),
    ('Needs Revision', 'Needs Revision'),
    ('Rejected', 'Rejected')
]

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class StudentRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    register_no = StringField('Register Number', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    department = SelectField('Department', choices=DEPARTMENTS, validators=[DataRequired()])
    year = SelectField('Academic Year', choices=YEARS, coerce=int, validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register as Student')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('Email address already registered.')

    def validate_register_no(self, field):
        if User.query.filter_by(register_no=field.data.strip()).first():
            raise ValidationError('Register number already registered.')

class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField('Current Password (leave blank if not changing)')
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6, message='New password must be at least 6 characters long')
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='New passwords must match')
    ])
    submit = SubmitField('Update Profile')

class AdminUserForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    register_no = StringField('Register Number (Students only)', validators=[Optional()])
    role = SelectField('Role', choices=ROLES, validators=[DataRequired()])
    department = SelectField('Department', choices=[('', '-- Select Department --')] + DEPARTMENTS, validators=[Optional()])
    year = SelectField('Year (Students only)', choices=[(0, '-- Select Year --')] + YEARS, coerce=int, validators=[Optional()])
    password = PasswordField('Password (leave empty to keep current when editing)', validators=[Optional(), Length(min=6)])
    is_active = BooleanField('Active Account', default=True)
    submit = SubmitField('Save User')

class AssignmentForm(FlaskForm):
    title = StringField('Assignment Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description / Requirements', validators=[DataRequired()])
    department = SelectField('Target Department', choices=DEPARTMENTS, validators=[DataRequired()])
    year = SelectField('Target Year', choices=YEARS, coerce=int, validators=[DataRequired()])
    max_marks = FloatField('Maximum Marks', default=100.0, validators=[DataRequired(), NumberRange(min=1, max=1000)])
    deadline = DateTimeLocalField('Submission Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    allow_late = BooleanField('Allow Late Submissions', default=True)
    attachment = FileField('Optional Guide/Attachment Document')
    submit = SubmitField('Save Assignment')

class SubmissionForm(FlaskForm):
    report_file = FileField('Project Report (PDF only, max 10MB)', validators=[DataRequired()])
    code_file = FileField('Source Code (ZIP archive only, max 25MB)', validators=[DataRequired()])
    remarks = TextAreaField('Remarks / Submission Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit Project')

class EvaluationForm(FlaskForm):
    marks = FloatField('Marks Awarded', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Evaluation Status', choices=STATUS_CHOICES, validators=[DataRequired()])
    feedback = TextAreaField('Detailed Faculty Feedback', validators=[DataRequired(), Length(min=5)])
    submit = SubmitField('Submit Evaluation')

class ReportFilterForm(FlaskForm):
    assignment_id = SelectField('Assignment', coerce=int, validators=[Optional()])
    department = SelectField('Department', choices=[('all', 'All Departments')] + DEPARTMENTS, validators=[Optional()])
    submit = SubmitField('Apply Filters')
