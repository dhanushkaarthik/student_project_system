from functools import wraps
from flask import session, redirect, url_for, flash, abort, request, g

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not g.current_user:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if not g.current_user.is_active:
            session.clear()
            flash('Your account has been deactivated. Please contact the administrator.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorator to enforce role-based access control.
    Usage: @role_required('admin') or @role_required('faculty', 'admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or not g.current_user:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            if not g.current_user.is_active:
                session.clear()
                flash('Your account has been deactivated. Please contact the administrator.', 'danger')
                return redirect(url_for('auth.login'))
            if g.current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
