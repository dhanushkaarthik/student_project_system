from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g
from app.extensions import db
from app.models import Notification
from app.decorators import login_required

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def index():
    user_notifications = Notification.query.filter_by(user_id=g.current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=user_notifications)

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    notif = Notification.query.get_or_404(notification_id)
    if notif.user_id != g.current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    notif.is_read = True
    db.session.commit()
    
    if request.is_json:
        return jsonify({'success': True, 'id': notif.id})
        
    next_page = request.referrer or url_for('notifications.index')
    return redirect(next_page)

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=g.current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    if request.is_json:
        return jsonify({'success': True})
        
    flash('All notifications marked as read.', 'info')
    return redirect(request.referrer or url_for('notifications.index'))

@notifications_bp.route('/api/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(user_id=g.current_user.id, is_read=False).count()
    return jsonify({'unread_count': count})
