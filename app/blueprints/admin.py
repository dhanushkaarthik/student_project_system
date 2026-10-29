from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, g, abort
from sqlalchemy import func
from app.extensions import db
from app.models import User, Assignment, Submission, Evaluation, ActivityLog
from app.forms import AdminUserForm
from app.decorators import role_required
from app.utils import log_activity

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    total_students = User.query.filter_by(role='student').count()
    total_faculty = User.query.filter_by(role='faculty').count()
    total_assignments = Assignment.query.count()
    
    latest_submissions = Submission.query.filter_by(is_latest=True).all()
    total_submissions = len(latest_submissions)
    evaluated_count = sum(1 for s in latest_submissions if s.evaluation is not None)
    pending_evaluations = total_submissions - evaluated_count
    late_submissions = sum(1 for s in latest_submissions if s.is_late)
    
    # 1. Submissions per assignment
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).limit(8).all()
    assg_names = [a.title[:18] + ('...' if len(a.title) > 18 else '') for a in assignments]
    assg_sub_counts = [len([s for s in latest_submissions if s.assignment_id == a.id]) for a in assignments]
    
    # 2. Status distribution
    status_counts = {
        'Approved': sum(1 for s in latest_submissions if s.status == 'Approved'),
        'Needs Revision': sum(1 for s in latest_submissions if s.status == 'Needs Revision'),
        'Rejected': sum(1 for s in latest_submissions if s.status == 'Rejected'),
        'Under Review': sum(1 for s in latest_submissions if s.status == 'Under Review'),
        'Submitted': sum(1 for s in latest_submissions if s.status == 'Submitted')
    }
    
    # 3. Monthly submission trend
    # Group submissions by Year-Month
    all_subs = Submission.query.all()
    monthly_data = {}
    for s in all_subs:
        m_key = s.submitted_at.strftime('%b %Y')
        monthly_data[m_key] = monthly_data.get(m_key, 0) + 1
    monthly_labels = list(monthly_data.keys())[-6:] if monthly_data else ['Current Month']
    monthly_counts = [monthly_data.get(k, 0) for k in monthly_labels]
    
    # 4. Average marks per assignment
    assg_avg_marks = []
    for a in assignments:
        assg_subs = [s for s in latest_submissions if s.assignment_id == a.id and s.evaluation is not None]
        if assg_subs:
            avg = sum(s.evaluation.marks for s in assg_subs) / len(assg_subs)
            assg_avg_marks.append(round(avg, 1))
        else:
            assg_avg_marks.append(0.0)
            
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    
    stats = {
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'pending_evaluations': pending_evaluations,
        'late_submissions': late_submissions
    }
    
    charts = {
        'assg_names': assg_names,
        'assg_sub_counts': assg_sub_counts,
        'status_labels': list(status_counts.keys()),
        'status_counts': list(status_counts.values()),
        'monthly_labels': monthly_labels,
        'monthly_counts': monthly_counts,
        'assg_avg_marks': assg_avg_marks
    }
    
    return render_template('admin/dashboard.html', stats=stats, charts=charts, logs=recent_logs)

@admin_bp.route('/users')
@role_required('admin')
def users():
    role_filter = request.args.get('role', 'all')
    dept_filter = request.args.get('department', 'all')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    query = User.query
    if role_filter != 'all':
        query = query.filter_by(role=role_filter)
    if dept_filter != 'all':
        query = query.filter_by(department=dept_filter)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.name.ilike(search_pattern)) | 
            (User.email.ilike(search_pattern)) | 
            (User.register_no.ilike(search_pattern))
        )
        
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'admin/users.html',
        users=pagination.items,
        pagination=pagination,
        role_filter=role_filter,
        dept_filter=dept_filter,
        search=search
    )

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@role_required('admin')
def new_user():
    form = AdminUserForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered for another user.', 'danger')
            return render_template('admin/user_form.html', form=form, title='Create New User')
            
        if not form.password.data:
            flash('Password is required for new users.', 'danger')
            return render_template('admin/user_form.html', form=form, title='Create New User')
            
        user = User(
            name=form.name.data.strip(),
            email=email,
            register_no=form.register_no.data.strip() if form.register_no.data else None,
            role=form.role.data,
            department=form.department.data if form.department.data else None,
            year=form.year.data if form.year.data and form.year.data > 0 else None,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        log_activity(g.current_user.id, 'Create User', f"Admin created user {user.email} ({user.role})")
        flash(f"User {user.name} created successfully!", 'success')
        return redirect(url_for('admin.users'))
        
    return render_template('admin/user_form.html', form=form, title='Create New User')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminUserForm(obj=user)
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if email != user.email:
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash('Email already registered for another user.', 'danger')
                return render_template('admin/user_form.html', form=form, title='Edit User', user=user)
            user.email = email
            
        user.name = form.name.data.strip()
        user.role = form.role.data
        user.department = form.department.data if form.department.data else None
        user.year = form.year.data if form.year.data and form.year.data > 0 else None
        user.register_no = form.register_no.data.strip() if form.register_no.data else None
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
            
        db.session.commit()
        log_activity(g.current_user.id, 'Edit User', f"Admin updated user {user.email}")
        flash(f"User {user.name} updated successfully!", 'success')
        return redirect(url_for('admin.users'))
        
    return render_template('admin/user_form.html', form=form, title='Edit User', user=user)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@role_required('admin')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == g.current_user.id:
        flash('You cannot deactivate your own administrative account.', 'warning')
        return redirect(url_for('admin.users'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    action_str = "activated" if user.is_active else "deactivated"
    log_activity(g.current_user.id, 'Toggle User Status', f"User {user.email} {action_str}")
    flash(f"User {user.name} has been {action_str}.", 'info')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@role_required('admin')
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_pw = request.form.get('new_password', 'Password@123').strip()
    if len(new_pw) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return redirect(url_for('admin.users'))
        
    user.set_password(new_pw)
    db.session.commit()
    
    log_activity(g.current_user.id, 'Reset Password', f"Admin reset password for user {user.email}")
    flash(f"Password for {user.name} was successfully reset.", 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == g.current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
        
    name = user.name
    email = user.email
    db.session.delete(user)
    db.session.commit()
    
    log_activity(g.current_user.id, 'Delete User', f"Admin deleted user {email}")
    flash(f"User {name} ({email}) was deleted successfully.", 'info')
    return redirect(url_for('admin.users'))

@admin_bp.route('/assignments')
@role_required('admin')
def assignments():
    dept_filter = request.args.get('department', 'all')
    query = Assignment.query
    if dept_filter != 'all':
        query = query.filter_by(department=dept_filter)
    all_assignments = query.order_by(Assignment.created_at.desc()).all()
    return render_template('admin/assignments.html', assignments=all_assignments, dept_filter=dept_filter)

@admin_bp.route('/submissions')
@role_required('admin')
def submissions():
    status_filter = request.args.get('status', 'all')
    late_filter = request.args.get('late', 'all')
    
    query = Submission.query.filter_by(is_latest=True)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if late_filter == 'yes':
        query = query.filter_by(is_late=True)
    elif late_filter == 'no':
        query = query.filter_by(is_late=False)
        
    all_submissions = query.order_by(Submission.submitted_at.desc()).all()
    return render_template(
        'admin/submissions.html',
        submissions=all_submissions,
        status_filter=status_filter,
        late_filter=late_filter
    )
