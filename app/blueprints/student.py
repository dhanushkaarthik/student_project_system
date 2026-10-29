from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, g, abort, current_app
from app.extensions import db
from app.models import Assignment, Submission, Evaluation, User
from app.forms import SubmissionForm
from app.decorators import login_required, role_required
from app.utils import (
    validate_and_save_file, 
    send_upload_file, 
    log_activity, 
    create_notification, 
    is_submission_late,
    check_and_generate_deadline_notifications,
    ALLOWED_REPORT_MIMES,
    ALLOWED_CODE_MIMES
)

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@role_required('student')
def dashboard():
    # Trigger 24-hour deadline notifications dynamically
    check_and_generate_deadline_notifications(g.current_user)
    
    # Query assignments for student's department and year
    assignments = Assignment.query.filter_by(
        department=g.current_user.department,
        year=g.current_user.year
    ).order_by(Assignment.deadline.asc()).all()
    
    # Map each assignment to latest submission
    assignment_data = []
    total_assignments = len(assignments)
    submitted_count = 0
    evaluated_count = 0
    pending_count = 0
    total_marks_obtained = 0.0
    total_max_marks = 0.0
    chart_labels = []
    chart_scores = []
    
    for assg in assignments:
        latest_sub = Submission.query.filter_by(
            assignment_id=assg.id,
            student_id=g.current_user.id,
            is_latest=True
        ).first()
        
        status_label = 'Not Submitted'
        if latest_sub:
            submitted_count += 1
            if latest_sub.evaluation:
                status_label = 'Evaluated'
                evaluated_count += 1
                total_marks_obtained += latest_sub.evaluation.marks
                total_max_marks += assg.max_marks
                chart_labels.append(assg.title)
                score_pct = round((latest_sub.evaluation.marks / assg.max_marks) * 100, 1) if assg.max_marks else 0
                chart_scores.append(score_pct)
            elif latest_sub.status == 'Needs Revision':
                status_label = 'Resubmission Required'
            elif latest_sub.status == 'Under Review':
                status_label = 'Under Review'
                pending_count += 1
            else:
                status_label = 'Submitted'
                pending_count += 1
        else:
            if assg.is_past_deadline:
                status_label = 'Late / Missing'
                
        assignment_data.append({
            'assignment': assg,
            'submission': latest_sub,
            'status_label': status_label
        })
        
    avg_score = round((total_marks_obtained / total_max_marks * 100), 1) if total_max_marks > 0 else 0.0
    
    stats = {
        'total': total_assignments,
        'submitted': submitted_count,
        'evaluated': evaluated_count,
        'pending': pending_count,
        'avg_score': avg_score
    }
    
    return render_template(
        'student/dashboard.html',
        assignments_data=assignment_data,
        stats=stats,
        chart_labels=chart_labels,
        chart_scores=chart_scores,
        now=datetime.now(timezone.utc)
    )

@student_bp.route('/assignments/<int:assignment_id>', methods=['GET'])
@role_required('student')
def assignment_detail(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Verify assignment department and year match student
    if assignment.department != g.current_user.department or assignment.year != g.current_user.year:
        flash('You do not have access to this assignment.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    latest_sub = Submission.query.filter_by(
        assignment_id=assignment.id,
        student_id=g.current_user.id,
        is_latest=True
    ).first()
    
    all_versions = Submission.query.filter_by(
        assignment_id=assignment.id,
        student_id=g.current_user.id
    ).order_by(Submission.version.desc()).all()
    
    form = SubmissionForm()
    is_late_now = is_submission_late(assignment)
    
    return render_template(
        'student/assignment_detail.html',
        assignment=assignment,
        latest_sub=latest_sub,
        all_versions=all_versions,
        form=form,
        is_late_now=is_late_now,
        now=datetime.now(timezone.utc)
    )

@student_bp.route('/submit/<int:assignment_id>', methods=['POST'])
@role_required('student')
def submit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if assignment.department != g.current_user.department or assignment.year != g.current_user.year:
        flash('You cannot submit to this assignment.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    now = datetime.now(timezone.utc)
    late = is_submission_late(assignment, now)
    
    if late and not assignment.allow_late:
        flash('The deadline for this assignment has passed and late submissions are strictly disabled.', 'danger')
        return redirect(url_for('student.assignment_detail', assignment_id=assignment.id))
        
    form = SubmissionForm()
    if not form.validate_on_submit():
        flash('Please provide both the PDF project report and ZIP source code archive.', 'danger')
        return redirect(url_for('student.assignment_detail', assignment_id=assignment.id))
        
    # Validate and save Report (PDF)
    report_file = form.report_file.data
    report_path, report_err = validate_and_save_file(
        report_file,
        folder_category='reports',
        allowed_extensions=current_app.config['ALLOWED_REPORT_EXTENSIONS'],
        max_bytes=current_app.config['MAX_REPORT_SIZE'],
        allowed_mimes=ALLOWED_REPORT_MIMES
    )
    if report_err:
        flash(f'Report upload error: {report_err}', 'danger')
        return redirect(url_for('student.assignment_detail', assignment_id=assignment.id))
        
    # Validate and save Code (ZIP)
    code_file = form.code_file.data
    code_path, code_err = validate_and_save_file(
        code_file,
        folder_category='code',
        allowed_extensions=current_app.config['ALLOWED_CODE_EXTENSIONS'],
        max_bytes=current_app.config['MAX_CODE_SIZE'],
        allowed_mimes=ALLOWED_CODE_MIMES
    )
    if code_err:
        flash(f'Source code upload error: {code_err}', 'danger')
        return redirect(url_for('student.assignment_detail', assignment_id=assignment.id))
        
    # Check for previous submissions to handle versioning
    existing_subs = Submission.query.filter_by(
        assignment_id=assignment.id,
        student_id=g.current_user.id
    ).order_by(Submission.version.desc()).all()
    
    version = 1
    if existing_subs:
        version = existing_subs[0].version + 1
        for sub in existing_subs:
            sub.is_latest = False
            
    new_sub = Submission(
        assignment_id=assignment.id,
        student_id=g.current_user.id,
        version=version,
        report_path=report_path,
        code_path=code_path,
        remarks=form.remarks.data.strip() if form.remarks.data else None,
        submitted_at=now,
        is_late=late,
        status='Submitted',
        is_latest=True
    )
    
    db.session.add(new_sub)
    db.session.commit()
    
    # Notify Faculty
    create_notification(
        user_id=assignment.faculty_id,
        message=f"{g.current_user.name} submitted assignment '{assignment.title}' (v{version}){' [LATE]' if late else ''}.",
        link=url_for('faculty.assignment_submissions', assignment_id=assignment.id)
    )
    
    log_activity(
        g.current_user.id,
        'Project Submission',
        f"Submitted v{version} for '{assignment.title}'. Late: {late}"
    )
    
    flash(f"Assignment submitted successfully (Version {version})!{' Marked as late submission.' if late else ''}", 'success')
    return redirect(url_for('student.assignment_detail', assignment_id=assignment.id))

@student_bp.route('/history')
@role_required('student')
def history():
    submissions = Submission.query.filter_by(student_id=g.current_user.id)\
        .order_by(Submission.submitted_at.desc()).all()
    return render_template('student/history.html', submissions=submissions)

@student_bp.route('/download/<int:submission_id>/<file_type>')
@role_required('student', 'faculty', 'admin')
def download_submission_file(submission_id, file_type):
    submission = Submission.query.get_or_404(submission_id)
    
    # Authorization: Student must own the submission, or user must be faculty of assignment or admin
    if g.current_user.is_student and submission.student_id != g.current_user.id:
        abort(403)
    if g.current_user.is_faculty and submission.assignment.faculty_id != g.current_user.id:
        abort(403)
        
    if file_type == 'report':
        path = submission.report_path
        name = f"Report_{submission.student.register_no or submission.student.id}_v{submission.version}.pdf"
    elif file_type == 'code':
        path = submission.code_path
        name = f"Code_{submission.student.register_no or submission.student.id}_v{submission.version}.zip"
    else:
        abort(404)
        
    return send_upload_file(path, as_attachment=True, download_name=name)

@student_bp.route('/download-attachment/<int:assignment_id>')
@login_required
def download_assignment_attachment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    if not assignment.attachment_path:
        abort(404, description="No attachment for this assignment.")
    return send_upload_file(assignment.attachment_path, as_attachment=True, download_name=assignment.attachment_filename)
