import io
from datetime import datetime, timezone, timedelta
from app.models import Assignment, Submission
from app.extensions import db
from tests.conftest import make_dummy_pdf_bytes, make_dummy_zip_bytes

def test_late_submission_allowed(client, app, seed_users):
    now = datetime.now(timezone.utc)
    
    with app.app_context():
        assg = Assignment(
            title="Past Due Lab (Late Allowed)",
            description="Testing late upload handling",
            faculty_id=seed_users['faculty_id'],
            department="Computer Science",
            year=3,
            max_marks=100.0,
            deadline=now - timedelta(days=1),  # In the past
            allow_late=True
        )
        db.session.add(assg)
        db.session.commit()
        assg_id = assg.id
        
    client.post('/login', data={'email': 'student@test.com', 'password': 'Student@123'})
    
    res = client.post(f'/student/submit/{assg_id}', data={
        'report_file': (io.BytesIO(make_dummy_pdf_bytes()), 'late_report.pdf'),
        'code_file': (io.BytesIO(make_dummy_zip_bytes()), 'late_code.zip'),
    }, content_type='multipart/form-data', follow_redirects=True)
    
    assert res.status_code == 200
    assert b"Marked as late submission" in res.data
    
    with app.app_context():
        sub = Submission.query.filter_by(assignment_id=assg_id, student_id=seed_users['student_id']).first()
        assert sub is not None
        assert sub.is_late is True

def test_late_submission_blocked_when_disallowed(client, app, seed_users):
    now = datetime.now(timezone.utc)
    
    with app.app_context():
        assg = Assignment(
            title="Past Due Lab (Late Disallowed)",
            description="Testing blocked upload",
            faculty_id=seed_users['faculty_id'],
            department="Computer Science",
            year=3,
            max_marks=100.0,
            deadline=now - timedelta(days=1),  # In the past
            allow_late=False  # Block late uploads!
        )
        db.session.add(assg)
        db.session.commit()
        assg_id = assg.id
        
    client.post('/login', data={'email': 'student@test.com', 'password': 'Student@123'})
    
    res = client.post(f'/student/submit/{assg_id}', data={
        'report_file': (io.BytesIO(make_dummy_pdf_bytes()), 'late_report.pdf'),
        'code_file': (io.BytesIO(make_dummy_zip_bytes()), 'late_code.zip'),
    }, content_type='multipart/form-data', follow_redirects=True)
    
    assert res.status_code == 200
    assert b"late submissions are strictly disabled" in res.data
    
    with app.app_context():
        sub = Submission.query.filter_by(assignment_id=assg_id, student_id=seed_users['student_id']).first()
        assert sub is None
