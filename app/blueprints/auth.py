from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g
from app.extensions import db
from app.models import User
from app.forms import LoginForm, StudentRegistrationForm, ProfileForm
from app.decorators import login_required
from app.utils import log_activity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.current_user:
        # Redirect already logged-in users to their respective dashboard
        if g.current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif g.current_user.is_faculty:
            return redirect(url_for('faculty.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
            
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('auth/login.html', form=form)
                
            session.clear()
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.name
            session.permanent = form.remember_me.data
            
            log_activity(user.id, 'User Login', f'{user.role.title()} logged in from {request.remote_addr}')
            flash(f'Welcome back, {user.name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
                
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif user.is_faculty:
                return redirect(url_for('faculty.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if g.current_user:
        return redirect(url_for('auth.login'))
        
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            register_no=form.register_no.data.strip(),
            department=form.department.data,
            year=form.year.data,
            role='student',
            is_active=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        log_activity(user.id, 'Student Registration', f'New student registered: {user.register_no}')
        flash('Registration successful! You can now log in with your credentials.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_activity(user_id, 'User Logout', 'User logged out')
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=g.current_user)
    if form.validate_on_submit():
        # Check email uniqueness if changed
        new_email = form.email.data.lower().strip()
        if new_email != g.current_user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing:
                flash('This email is already taken by another account.', 'danger')
                return render_template('auth/profile.html', form=form)
            g.current_user.email = new_email
            
        g.current_user.name = form.name.data.strip()
        session['user_name'] = g.current_user.name
        
        # Handle password change
        if form.new_password.data:
            if not form.current_password.data:
                flash('Please provide your current password to set a new password.', 'danger')
                return render_template('auth/profile.html', form=form)
            if not g.current_user.check_password(form.current_password.data):
                flash('Current password entered is incorrect.', 'danger')
                return render_template('auth/profile.html', form=form)
            g.current_user.set_password(form.new_password.data)
            flash('Profile and password updated successfully!', 'success')
        else:
            flash('Profile updated successfully!', 'success')
            
        db.session.commit()
        log_activity(g.current_user.id, 'Profile Updated', 'User modified profile details')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html', form=form)
