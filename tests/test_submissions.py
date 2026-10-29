import io
from datetime import datetime, timezone, timedelta
from app.models import Assignment, Submission
from app.extensions import db
from tests.conftest import make_dummy_pdf_bytes, make_dummy_zip_bytes

def test_submission_and_versioning(client, app, seed_users):
    now = datetime.now(timezone.utc)
    
    with app.app_context():
        assg = Assignment(
            title="Algorithm Test Lab",
            description="Test assignment description",
            faculty_id=seed_users['faculty_id'],
            department="Computer Science",
            year=3,
            max_marks=100.0,
            deadline=now + timedelta(days=2),
            allow_late=True
        )
        db.session.add(assg)
        db.session.commit()
        assg_id = assg.id
        
    client.post('/login', data={'email': 'student@test.com', 'password': 'Student@123'})
    
    # 1. First submission (version 1)
    res = client.post(f'/student/submit/{assg_id}', data={
        'report_file': (io.BytesIO(make_dummy_pdf_bytes()), 'report.pdf'),
        'code_file': (io.BytesIO(make_dummy_zip_bytes()), 'code.zip'),
        'remarks': 'First draft submission'
    }, content_type='multipart/form-data', follow_redirects=True)
    
    assert res.status_code == 200
    assert b"Assignment submitted successfully" in res.data
    
    with app.app_context():
        sub1 = Submission.query.filter_by(assignment_id=assg_id, student_id=seed_users['student_id'], version=1).first()
        assert sub1 is not None
        assert sub1.version == 1
        assert sub1.is_latest is True
        assert sub1.is_late is False
        
    # 2. Resubmission (version 2)
    res2 = client.post(f'/student/submit/{assg_id}', data={
        'report_file': (io.BytesIO(make_dummy_pdf_bytes()), 'report_v2.pdf'),
        'code_file': (io.BytesIO(make_dummy_zip_bytes()), 'code_v2.zip'),
        'remarks': 'Second revised submission'
    }, content_type='multipart/form-data', follow_redirects=True)
    
    assert res2.status_code == 200
    assert b"Version 2" in res2.data
    
    with app.app_context():
        subs = Submission.query.filter_by(assignment_id=assg_id, student_id=seed_users['student_id']).order_by(Submission.version.asc()).all()
        assert len(subs) == 2
        assert subs[0].version == 1 and subs[0].is_latest is False
        assert subs[1].version == 2 and subs[1].is_latest is True

def test_submission_invalid_file_extension(client, app, seed_users):
    now = datetime.now(timezone.utc)
    with app.app_context():
        assg = Assignment(
            title="Validation Test Lab",
            description="Testing extensions",
            faculty_id=seed_users['faculty_id'],
            department="Computer Science",
            year=3,
            max_marks=100.0,
            deadline=now + timedelta(days=2),
            allow_late=True
        )
        db.session.add(assg)
        db.session.commit()
        assg_id = assg.id
        
    client.post('/login', data={'email': 'student@test.com', 'password': 'Student@123'})
    
    # Try uploading .txt instead of .pdf
    res = client.post(f'/student/submit/{assg_id}', data={
        'report_file': (io.BytesIO(b"not a pdf"), 'report.txt'),
        'code_file': (io.BytesIO(make_dummy_zip_bytes()), 'code.zip'),
    }, content_type='multipart/form-data', follow_redirects=True)
    
    assert b"Invalid file type .txt" in res.data
