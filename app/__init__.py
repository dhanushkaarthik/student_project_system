import os
from datetime import datetime, timezone
from flask import Flask, redirect, url_for, session, g, render_template
from config import Config
from app.extensions import db, csrf
from app.models import User, Notification

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure upload subfolders and instance directory exist
    for sub in ['reports', 'code', 'assignment_files']:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], sub), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    
    # Load current user before each request
    @app.before_request
    def load_logged_in_user():
        user_id = session.get('user_id')
        if user_id is None:
            g.current_user = None
        else:
            g.current_user = db.session.get(User, user_id)
            
    # Context processor to make current_user and notifications available in all templates
    @app.context_processor
    def inject_user_and_notifications():
        if g.current_user:
            notifs = Notification.query.filter_by(
                user_id=g.current_user.id
            ).order_by(Notification.created_at.desc()).limit(5).all()
            
            unread_count = Notification.query.filter_by(
                user_id=g.current_user.id,
                is_read=False
            ).count()
            
            return {
                'current_user': g.current_user,
                'navbar_notifications': notifs,
                'unread_notif_count': unread_count
            }
        return {
            'current_user': None,
            'navbar_notifications': [],
            'unread_notif_count': 0
        }
        
    # Custom Jinja filters
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%b %d, %Y %I:%M %p'):
        if value is None:
            return ""
        return value.strftime(format)
        
    @app.template_filter('status_badge')
    def status_badge(status):
        badges = {
            'Approved': 'badge bg-success',
            'Evaluated': 'badge bg-success',
            'Submitted': 'badge bg-primary',
            'Under Review': 'badge bg-info text-dark',
            'Needs Revision': 'badge bg-warning text-dark',
            'Rejected': 'badge bg-danger',
            'Late': 'badge bg-danger',
            'Not Submitted': 'badge bg-secondary',
            'Late / Missing': 'badge bg-danger'
        }
        return badges.get(status, 'badge bg-secondary')
        
    # Root route
    @app.route('/')
    def index():
        if g.current_user:
            if g.current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif g.current_user.is_faculty:
                return redirect(url_for('faculty.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))
        
    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.student import student_bp
    from app.blueprints.faculty import faculty_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.notifications import notifications_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    
    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
        
    return app
