import os
import uuid
from datetime import datetime, timezone, timedelta
from werkzeug.utils import secure_filename
from flask import current_app, abort, send_from_directory
from app.extensions import db
from app.models import Notification, ActivityLog, Assignment, Submission

# Allowed MIME prefixes and types
ALLOWED_REPORT_MIMES = {'application/pdf', 'application/x-pdf'}
ALLOWED_CODE_MIMES = {'application/zip', 'application/x-zip-compressed', 'multipart/x-zip', 'application/x-zip'}

def allowed_file(filename, allowed_extensions):
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions

def validate_and_save_file(file_storage, folder_category, allowed_extensions, max_bytes, allowed_mimes=None):
    """
    Validates file extension, MIME type, and size limit, then saves securely.
    Returns (saved_relative_path, error_message).
    """
    if not file_storage or file_storage.filename == '':
        return None, "No file selected."
    
    filename = secure_filename(file_storage.filename)
    if not filename:
        filename = f"file_{uuid.uuid4().hex[:8]}"
        
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext not in allowed_extensions:
        return None, f"Invalid file type .{ext}. Allowed: {', '.join(allowed_extensions)}"
    
    # Check MIME type if provided
    if allowed_mimes and file_storage.mimetype and file_storage.mimetype.lower() not in allowed_mimes:
        # Fallback check: sometimes browsers send octet-stream for zip
        if not (ext == 'zip' and file_storage.mimetype in ['application/octet-stream', 'application/zip', 'application/x-zip-compressed']):
            return None, f"Invalid MIME type ({file_storage.mimetype}) for .{ext} file."
        
    # Check file size (seek to end)
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    
    if size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        return None, f"File exceeds maximum allowed size of {max_mb:.0f} MB."
        
    if size == 0:
        return None, "The uploaded file is empty."
        
    # Generate unique filename to avoid overwrites and collisions
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_category)
    os.makedirs(target_dir, exist_ok=True)
    
    target_path = os.path.join(target_dir, unique_name)
    file_storage.save(target_path)
    
    # Store relative path from UPLOAD_FOLDER
    relative_path = os.path.join(folder_category, unique_name).replace('\\', '/')
    return relative_path, None

def check_safe_path(base_dir, path):
    """Ensure path stays within base_dir to prevent path traversal."""
    resolved_path = os.path.abspath(os.path.join(base_dir, path))
    resolved_base = os.path.abspath(base_dir)
    return resolved_path.startswith(resolved_base) and os.path.exists(resolved_path)

def send_upload_file(relative_path, as_attachment=True, download_name=None):
    """Safely send file from UPLOAD_FOLDER."""
    upload_dir = current_app.config['UPLOAD_FOLDER']
    full_path = os.path.join(upload_dir, relative_path)
    
    if not check_safe_path(upload_dir, relative_path):
        abort(404, description="File not found or invalid path.")
        
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    return send_from_directory(directory, filename, as_attachment=as_attachment, download_name=download_name)

def log_activity(user_id, action, details=None):
    """Records an action in the ActivityLog."""
    try:
        log = ActivityLog(user_id=user_id, action=action, details=details)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to log activity: {e}")

def create_notification(user_id, message, link=None):
    """Creates a single in-app notification."""
    try:
        notif = Notification(user_id=user_id, message=message, link=link)
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create notification: {e}")
        return None

def notify_users(user_ids, message, link=None):
    """Bulk create notifications for multiple users."""
    try:
        for uid in user_ids:
            notif = Notification(user_id=uid, message=message, link=link)
            db.session.add(notif)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to notify users: {e}")

def is_submission_late(assignment, submit_time=None):
    """
    Checks if a submission is past the assignment deadline.
    Returns boolean (True if late, False otherwise).
    """
    if submit_time is None:
        submit_time = datetime.now(timezone.utc)
    elif submit_time.tzinfo is None:
        submit_time = submit_time.replace(tzinfo=timezone.utc)
        
    deadline = assignment.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
        
    return submit_time > deadline

def check_and_generate_deadline_notifications(user):
    """
    Trigger deadline approaching notifications for students:
    if deadline is within next 24 hours and not yet submitted.
    """
    if not user or user.role != 'student':
        return
        
    now = datetime.now(timezone.utc)
    in_24_hours = now + timedelta(hours=24)
    
    # Query assignments for student's department and year where deadline is between now and in_24_hours
    assignments = Assignment.query.filter(
        Assignment.department == user.department,
        Assignment.year == user.year,
        Assignment.deadline > now,
        Assignment.deadline <= in_24_hours
    ).all()
    
    for assg in assignments:
        # Check if student has already submitted
        sub = Submission.query.filter_by(assignment_id=assg.id, student_id=user.id, is_latest=True).first()
        if not sub:
            # Check if notification already exists to avoid spamming
            existing = Notification.query.filter(
                Notification.user_id == user.id,
                Notification.message.like(f"%'{assg.title}' is due in less than 24 hours%")
            ).first()
            if not existing:
                create_notification(
                    user_id=user.id,
                    message=f"Reminder: Assignment '{assg.title}' is due in less than 24 hours!",
                    link=f"/student/assignments/{assg.id}"
                )
