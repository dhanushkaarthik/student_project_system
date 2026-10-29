import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request, Response, g
from app.models import Assignment, Submission, User
from app.decorators import role_required

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@role_required('admin', 'faculty')
def index():
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    if g.current_user.is_faculty:
        assignments = [a for a in assignments if a.faculty_id == g.current_user.id]
        
    assignment_id = request.args.get('assignment_id', type=int)
    department = request.args.get('department', 'all')
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')
    
    query = Submission.query.filter_by(is_latest=True)
    
    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)
    elif g.current_user.is_faculty:
        assg_ids = [a.id for a in assignments]
        query = query.filter(Submission.assignment_id.in_(assg_ids)) if assg_ids else query.filter(Submission.id == -1)
        
    if department != 'all':
        query = query.join(User, Submission.student_id == User.id).filter(User.department == department)
        
    if date_from_str:
        try:
            d_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            query = query.filter(Submission.submitted_at >= d_from)
        except ValueError:
            pass
            
    if date_to_str:
        try:
            d_to = datetime.strptime(date_to_str, '%Y-%m-%d')
            query = query.filter(Submission.submitted_at <= d_to)
        except ValueError:
            pass
            
    submissions = query.order_by(Submission.submitted_at.desc()).all()
    
    return render_template(
        'admin/reports.html',
        assignments=assignments,
        submissions=submissions,
        selected_assignment=assignment_id,
        selected_department=department,
        date_from=date_from_str,
        date_to=date_to_str
    )

@reports_bp.route('/export-csv')
@role_required('admin', 'faculty')
def export_csv():
    assignment_id = request.args.get('assignment_id', type=int)
    department = request.args.get('department', 'all')
    
    query = Submission.query.filter_by(is_latest=True)
    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)
    elif g.current_user.is_faculty:
        faculty_assg_ids = [a.id for a in Assignment.query.filter_by(faculty_id=g.current_user.id).all()]
        query = query.filter(Submission.assignment_id.in_(faculty_assg_ids))
        
    if department != 'all':
        query = query.join(User, Submission.student_id == User.id).filter(User.department == department)
        
    submissions = query.order_by(Submission.submitted_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Submission ID',
        'Student Name',
        'Register Number',
        'Department',
        'Year',
        'Assignment Title',
        'Version',
        'Submission Date (UTC)',
        'Is Late',
        'Marks Awarded',
        'Maximum Marks',
        'Percentage (%)',
        'Evaluation Status',
        'Faculty Feedback'
    ])
    
    for s in submissions:
        marks = s.evaluation.marks if s.evaluation else 'N/A'
        max_marks = s.assignment.max_marks
        pct = f"{(s.evaluation.marks / max_marks * 100):.1f}%" if s.evaluation and max_marks else 'N/A'
        feedback = s.evaluation.feedback if s.evaluation else ''
        
        writer.writerow([
            s.id,
            s.student.name,
            s.student.register_no or '',
            s.student.department or '',
            f"Year {s.student.year}" if s.student.year else '',
            s.assignment.title,
            s.version,
            s.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Yes' if s.is_late else 'No',
            marks,
            max_marks,
            pct,
            s.status,
            feedback
        ])
        
    output.seek(0)
    filename = f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@reports_bp.route('/printable')
@role_required('admin', 'faculty')
def printable():
    assignment_id = request.args.get('assignment_id', type=int)
    department = request.args.get('department', 'all')
    
    assignment = None
    if assignment_id:
        assignment = db.session.get(Assignment, assignment_id)
        
    query = Submission.query.filter_by(is_latest=True)
    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)
    elif g.current_user.is_faculty:
        faculty_assg_ids = [a.id for a in Assignment.query.filter_by(faculty_id=g.current_user.id).all()]
        query = query.filter(Submission.assignment_id.in_(faculty_assg_ids))
        
    if department != 'all':
        query = query.join(User, Submission.student_id == User.id).filter(User.department == department)
        
    submissions = query.order_by(Submission.submitted_at.desc()).all()
    
    # Calculate stats
    evaluated_subs = [s for s in submissions if s.evaluation]
    marks_list = [s.evaluation.marks for s in evaluated_subs]
    
    stats = {
        'total_submissions': len(submissions),
        'evaluated_count': len(evaluated_subs),
        'highest_mark': max(marks_list) if marks_list else 0,
        'lowest_mark': min(marks_list) if marks_list else 0,
        'average_mark': round(sum(marks_list) / len(marks_list), 1) if marks_list else 0,
        'late_count': sum(1 for s in submissions if s.is_late)
    }
    
    return render_template(
        'reports/printable_report.html',
        assignment=assignment,
        submissions=submissions,
        department=department,
        stats=stats,
        generated_at=datetime.now()
    )
