from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, g, abort, current_app
from app.extensions import db
from app.models import Assignment, Submission, Evaluation, User
from app.forms import AssignmentForm, EvaluationForm
from app.decorators import role_required
from app.utils import (
    validate_and_save_file, 
    log_activity, 
    create_notification, 
    notify_users
)

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.route('/dashboard')
@role_required('faculty')
def dashboard():
    assignments = Assignment.query.filter_by(faculty_id=g.current_user.id)\
        .order_by(Assignment.created_at.desc()).all()
        
    assignment_ids = [a.id for a in assignments]
    
    total_assignments = len(assignments)
    all_submissions = Submission.query.filter(
        Submission.assignment_id.in_(assignment_ids),
        Submission.is_latest == True
    ).all() if assignment_ids else []
    
    total_submissions = len(all_submissions)
    evaluated_count = sum(1 for s in all_submissions if s.evaluation is not None)
    pending_count = total_submissions - evaluated_count
    late_count = sum(1 for s in all_submissions if s.is_late)
    
    # Chart 1: Pending vs Evaluated
    chart_status_data = [pending_count, evaluated_count]
    
    # Chart 2: Average marks per assignment
    chart_assg_labels = []
    chart_assg_marks = []
    
    for assg in assignments:
        subs = [s for s in all_submissions if s.assignment_id == assg.id and s.evaluation is not None]
        chart_assg_labels.append(assg.title[:20] + ('...' if len(assg.title) > 20 else ''))
        if subs:
            avg_mark = sum(s.evaluation.marks for s in subs) / len(subs)
            chart_assg_marks.append(round(avg_mark, 1))
        else:
            chart_assg_marks.append(0)
            
    stats = {
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'pending_evaluations': pending_count,
        'evaluated_count': evaluated_count,
        'late_submissions': late_count
    }
    
    return render_template(
        'faculty/dashboard.html',
        assignments=assignments,
        stats=stats,
        chart_status_data=chart_status_data,
        chart_assg_labels=chart_assg_labels,
        chart_assg_marks=chart_assg_marks
    )

@faculty_bp.route('/assignments/new', methods=['GET', 'POST'])
@role_required('faculty')
def new_assignment():
    form = AssignmentForm()
    if form.validate_on_submit():
        attachment_path = None
        if form.attachment.data:
            path, err = validate_and_save_file(
                form.attachment.data,
                folder_category='assignment_files',
                allowed_extensions=current_app.config['ALLOWED_ATTACHMENT_EXTENSIONS'],
                max_bytes=current_app.config['MAX_ATTACHMENT_SIZE']
            )
            if err:
                flash(f'Attachment upload failed: {err}', 'danger')
                return render_template('faculty/assignment_form.html', form=form, title='Create Assignment')
            attachment_path = path
            
        assg = Assignment(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            faculty_id=g.current_user.id,
            department=form.department.data,
            year=form.year.data,
            max_marks=form.max_marks.data,
            deadline=form.deadline.data,
            allow_late=form.allow_late.data,
            attachment_path=attachment_path
        )
        db.session.add(assg)
        db.session.commit()
        
        # Notify matching students
        students = User.query.filter_by(
            role='student',
            department=assg.department,
            year=assg.year,
            is_active=True
        ).all()
        student_ids = [s.id for s in students]
        notify_users(
            student_ids,
            f"New assignment posted: '{assg.title}'. Deadline: {assg.deadline.strftime('%b %d, %Y %I:%M %p')}",
            link=f"/student/assignments/{assg.id}"
        )
        
        log_activity(g.current_user.id, 'Create Assignment', f"Created assignment '{assg.title}' for {assg.department} Y{assg.year}")
        flash('Assignment published successfully and students have been notified!', 'success')
        return redirect(url_for('faculty.dashboard'))
        
    return render_template('faculty/assignment_form.html', form=form, title='Create Assignment')

@faculty_bp.route('/assignments/<int:assignment_id>/edit', methods=['GET', 'POST'])
@role_required('faculty')
def edit_assignment(assignment_id):
    assg = Assignment.query.get_or_404(assignment_id)
    if assg.faculty_id != g.current_user.id:
        abort(403)
        
    form = AssignmentForm(obj=assg)
    if form.validate_on_submit():
        assg.title = form.title.data.strip()
        assg.description = form.description.data.strip()
        assg.department = form.department.data
        assg.year = form.year.data
        assg.max_marks = form.max_marks.data
        assg.deadline = form.deadline.data
        assg.allow_late = form.allow_late.data
        
        if form.attachment.data:
            path, err = validate_and_save_file(
                form.attachment.data,
                folder_category='assignment_files',
                allowed_extensions=current_app.config['ALLOWED_ATTACHMENT_EXTENSIONS'],
                max_bytes=current_app.config['MAX_ATTACHMENT_SIZE']
            )
            if err:
                flash(f'Attachment upload failed: {err}', 'danger')
                return render_template('faculty/assignment_form.html', form=form, title='Edit Assignment', assignment=assg)
            assg.attachment_path = path
            
        db.session.commit()
        log_activity(g.current_user.id, 'Edit Assignment', f"Updated assignment '{assg.title}'")
        flash('Assignment updated successfully!', 'success')
        return redirect(url_for('faculty.dashboard'))
        
    return render_template('faculty/assignment_form.html', form=form, title='Edit Assignment', assignment=assg)

@faculty_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@role_required('faculty')
def delete_assignment(assignment_id):
    assg = Assignment.query.get_or_404(assignment_id)
    if assg.faculty_id != g.current_user.id:
        abort(403)
        
    title = assg.title
    db.session.delete(assg)
    db.session.commit()
    
    log_activity(g.current_user.id, 'Delete Assignment', f"Deleted assignment '{title}'")
    flash(f"Assignment '{title}' and all associated submissions were deleted.", 'info')
    return redirect(url_for('faculty.dashboard'))

@faculty_bp.route('/assignments/<int:assignment_id>/submissions')
@role_required('faculty')
def assignment_submissions(assignment_id):
    assg = Assignment.query.get_or_404(assignment_id)
    if assg.faculty_id != g.current_user.id:
        abort(403)
        
    status_filter = request.args.get('status', 'all')
    late_filter = request.args.get('late', 'all')
    
    query = Submission.query.filter_by(assignment_id=assg.id, is_latest=True)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if late_filter == 'yes':
        query = query.filter_by(is_late=True)
    elif late_filter == 'no':
        query = query.filter_by(is_late=False)
        
    submissions = query.order_by(Submission.submitted_at.desc()).all()
    
    return render_template(
        'faculty/assignment_submissions.html',
        assignment=assg,
        submissions=submissions,
        status_filter=status_filter,
        late_filter=late_filter
    )

@faculty_bp.route('/submissions/<int:submission_id>/evaluate', methods=['GET', 'POST'])
@role_required('faculty')
def evaluate_submission(submission_id):
    sub = Submission.query.get_or_404(submission_id)
    assg = sub.assignment
    if assg.faculty_id != g.current_user.id:
        abort(403)
        
    # When faculty opens the submission, if status is 'Submitted', set it to 'Under Review'
    if sub.status == 'Submitted':
        sub.status = 'Under Review'
        db.session.commit()
        
    evaluation = sub.evaluation
    form = EvaluationForm(obj=evaluation)
    
    if form.validate_on_submit():
        marks = form.marks.data
        if marks > assg.max_marks:
            flash(f"Marks awarded ({marks}) cannot exceed maximum allowed marks ({assg.max_marks}).", 'danger')
            return render_template('faculty/evaluate.html', submission=sub, assignment=assg, form=form)
            
        status = form.status.data
        sub.status = status
        
        if evaluation:
            evaluation.marks = marks
            evaluation.feedback = form.feedback.data.strip()
            evaluation.evaluated_at = datetime.now(timezone.utc)
        else:
            evaluation = Evaluation(
                submission_id=sub.id,
                faculty_id=g.current_user.id,
                marks=marks,
                feedback=form.feedback.data.strip(),
                evaluated_at=datetime.now(timezone.utc)
            )
            db.session.add(evaluation)
            
        db.session.commit()
        
        # Student notification
        if status == 'Needs Revision':
            notif_msg = f"Revision requested for '{assg.title}'. Please review feedback and resubmit."
        else:
            notif_msg = f"Your submission for '{assg.title}' was evaluated. Marks: {marks}/{assg.max_marks} ({status})."
            
        create_notification(
            user_id=sub.student_id,
            message=notif_msg,
            link=f"/student/assignments/{assg.id}"
        )
        
        log_activity(
            g.current_user.id,
            'Evaluate Submission',
            f"Evaluated sub #{sub.id} (Student: {sub.student.name}) - Marks: {marks}/{assg.max_marks}, Status: {status}"
        )
        
        flash('Evaluation recorded and notification sent to student.', 'success')
        return redirect(url_for('faculty.assignment_submissions', assignment_id=assg.id))
        
    return render_template('faculty/evaluate.html', submission=sub, assignment=assg, form=form)
