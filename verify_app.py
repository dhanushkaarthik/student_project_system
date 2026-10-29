"""
End-to-end Verification Script for Student Project Submission and Evaluation Management System
"""
import io
import zipfile
from app import create_app
from app.models import User, Assignment, Submission, Evaluation, Notification, ActivityLog
from app.extensions import db

import re

def get_csrf_token(client, url):
    res = client.get(url)
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', res.data.decode('utf-8'))
    if match:
        return match.group(1)
    match = re.search(r'name="csrf-token"\s+content="([^"]+)"', res.data.decode('utf-8'))
    if match:
        return match.group(1)
    return ""

def test_full_system_flow():
    app = create_app()
    client = app.test_client()
    
    print("\n--- 1. Testing Root and Public Access ---")
    res = client.get('/', follow_redirects=True)
    assert res.status_code == 200
    assert b"Welcome to SPEMS" in res.data
    print("[OK] Public redirect to login works.")

    print("\n--- 2. Testing Student Self-Registration ---")
    import uuid
    rand_suffix = uuid.uuid4().hex[:6]
    token = get_csrf_token(client, '/register')
    reg_data = {
        'csrf_token': token,
        'name': f'Veronica Mars {rand_suffix}',
        'register_no': f'REG{rand_suffix.upper()}',
        'email': f'veronica_{rand_suffix}@college.edu',
        'department': 'Computer Science',
        'year': 3,
        'password': 'Password@123',
        'confirm_password': 'Password@123'
    }
    res = client.post('/register', data=reg_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Registration successful" in res.data
    print("[OK] Student self-registration succeeded.")

    print("\n--- 3. Testing Admin Authentication & Dashboard ---")
    token = get_csrf_token(client, '/login')
    res = client.post('/login', data={'csrf_token': token, 'email': 'admin@college.edu', 'password': 'Admin@123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Administrative Overview" in res.data
    assert b"submissionsPerAssgChart" in res.data
    assert b"statusDistChart" in res.data
    print("[OK] Admin login and dashboard charts loaded.")

    print("\n--- 4. Testing Admin User Management ---")
    res = client.get('/admin/users')
    assert res.status_code == 200
    assert b"User Management" in res.data
    assert b"Veronica Mars" in res.data

    token = get_csrf_token(client, '/admin/users/new')
    res = client.post('/admin/users/new', data={
        'csrf_token': token,
        'name': f'Dr. Nikola Tesla {rand_suffix}',
        'email': f'tesla_{rand_suffix}@college.edu',
        'role': 'faculty',
        'department': 'Electrical & Electronics',
        'password': 'Faculty@123',
        'is_active': 'y'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert f"Dr. Nikola Tesla {rand_suffix}".encode('utf-8') in res.data
    print("[OK] Admin created new faculty member.")

    res = client.get('/admin/assignments')
    assert res.status_code == 200
    assert b"System-wide Assignments" in res.data
    
    res = client.get('/admin/submissions')
    assert res.status_code == 200
    assert b"System-wide Submissions" in res.data
    print("[OK] Admin system-wide assignments and submissions views verified.")

    print("\n--- 5. Testing Report Export (CSV & Printable HTML) ---")
    res = client.get('/reports/export-csv')
    assert res.status_code == 200
    assert res.headers["Content-Type"].startswith("text/csv")
    assert b"Submission ID,Student Name,Register Number" in res.data
    print(f"[OK] CSV report generated ({len(res.data)} bytes).")

    res = client.get('/reports/printable')
    assert res.status_code == 200
    assert b"STUDENT PROJECT SUBMISSION & EVALUATION REPORT" in res.data
    assert b"window.print()" in res.data
    print("[OK] Printable HTML report generated.")

    print("\n--- 6. Testing Faculty Authentication & Assignment Creation ---")
    client.get('/logout', follow_redirects=True)
    token = get_csrf_token(client, '/login')
    res = client.post('/login', data={'csrf_token': token, 'email': 'sarah.faculty@college.edu', 'password': 'Faculty@123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Faculty Evaluation Dashboard" in res.data

    from datetime import datetime, timezone, timedelta
    deadline_str = (datetime.now(timezone.utc) + timedelta(days=7)).strftime('%Y-%m-%dT23:59')
    dummy_guide = (io.BytesIO(b"%PDF-1.4 sample guide doc"), "project_spec.pdf")
    
    token = get_csrf_token(client, '/faculty/assignments/new')
    res = client.post('/faculty/assignments/new', data={
        'csrf_token': token,
        'title': 'Autonomous Robotics Pathfinding System',
        'description': 'Implement A* and RRT algorithms on a grid environment with collision avoidance.',
        'department': 'Computer Science',
        'year': 3,
        'max_marks': '100.0',
        'deadline': deadline_str,
        'allow_late': 'y',
        'attachment': dummy_guide
    }, content_type='multipart/form-data', follow_redirects=True)
    assert res.status_code == 200
    assert b"Assignment published successfully" in res.data
    print("[OK] Faculty created new project assignment with attachment.")

    print("\n--- 7. Testing Student Workflow, Late Check, & File Upload ---")
    client.get('/logout', follow_redirects=True)
    token = get_csrf_token(client, '/login')
    res = client.post('/login', data={'csrf_token': token, 'email': 'alex.student@college.edu', 'password': 'Student@123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Student Project Portal" in res.data

    res = client.get('/notifications/')
    assert res.status_code == 200
    assert b"Autonomous Robotics Pathfinding System" in res.data
    print("[OK] Student received notification of new assignment.")

    with app.app_context():
        new_assg = Assignment.query.filter_by(title='Autonomous Robotics Pathfinding System').first()
        assg_id = new_assg.id

    res = client.get(f'/student/assignments/{assg_id}')
    assert res.status_code == 200
    assert b"Implement A* and RRT algorithms" in res.data
    assert b"data-deadline" in res.data

    pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj\n4 0 obj<</Length 10>>stream\nBT ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000216 00000 n \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n277\n%%EOF\n"
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('robotics.py', 'print("RRT execution")\n')
    zip_bytes = zip_buf.getvalue()

    token = get_csrf_token(client, f'/student/assignments/{assg_id}')
    res = client.post(f'/student/submit/{assg_id}', data={
        'csrf_token': token,
        'report_file': (io.BytesIO(pdf_bytes), 'alex_robotics_report.pdf'),
        'code_file': (io.BytesIO(zip_bytes), 'alex_robotics_code.zip'),
        'remarks': 'Implemented both A* and RRT with dynamic obstacle simulation.'
    }, content_type='multipart/form-data', follow_redirects=True)
    assert res.status_code == 200
    assert b"Assignment submitted successfully" in res.data
    print("[OK] Student uploaded PDF report and ZIP source code.")

    res = client.get('/student/history')
    assert res.status_code == 200
    assert b"Autonomous Robotics Pathfinding System" in res.data
    print("[OK] Submission reflected in student history.")

    print("\n--- 8. Testing Faculty Evaluation & Grade Entry ---")
    client.get('/logout', follow_redirects=True)
    token = get_csrf_token(client, '/login')
    client.post('/login', data={'csrf_token': token, 'email': 'sarah.faculty@college.edu', 'password': 'Faculty@123'}, follow_redirects=True)
    
    res = client.get(f'/faculty/assignments/{assg_id}/submissions')
    assert res.status_code == 200
    assert b"Alex Johnson" in res.data
    
    with app.app_context():
        sub = Submission.query.filter_by(assignment_id=assg_id, is_latest=True).first()
        sub_id = sub.id

    token = get_csrf_token(client, f'/faculty/submissions/{sub_id}/evaluate')
    res = client.post(f'/faculty/submissions/{sub_id}/evaluate', data={
        'csrf_token': token,
        'marks': '95.0',
        'status': 'Approved',
        'feedback': 'Excellent simulation results. Obstacle avoidance logic is robust and well documented.'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Evaluation recorded and notification sent" in res.data
    print("[OK] Faculty evaluated submission with marks, status, and feedback.")

    print("\n--- 9. Testing Student Evaluation Notification & Progress Graph ---")
    client.get('/logout', follow_redirects=True)
    token = get_csrf_token(client, '/login')
    client.post('/login', data={'csrf_token': token, 'email': 'alex.student@college.edu', 'password': 'Student@123'}, follow_redirects=True)
    
    res = client.get('/student/dashboard')
    assert res.status_code == 200
    assert b"studentProgressChart" in res.data
    assert b"95.0" in res.data or b"Evaluated" in res.data

    res = client.get('/notifications/')
    assert res.status_code == 200
    assert b"Autonomous Robotics Pathfinding System" in res.data
    assert b"was evaluated" in res.data
    print("[OK] Student received evaluation notification and score updated.")

    print("\n--- 10. Testing Notification Mark as Read & Profile Management ---")
    with app.app_context():
        notif = Notification.query.filter_by(user_id=User.query.filter_by(email='alex.student@college.edu').first().id, is_read=False).first()
        notif_id = notif.id if notif else None

    if notif_id:
        token = get_csrf_token(client, '/notifications/')
        res = client.post(f'/notifications/{notif_id}/read', data={'csrf_token': token}, follow_redirects=True)
        assert res.status_code == 200
        print("[OK] Notification marked as read successfully.")

    token = get_csrf_token(client, '/profile')
    res = client.post('/profile', data={
        'csrf_token': token,
        'name': 'Alex Johnson Jr.',
        'email': 'alex.student@college.edu',
        'current_password': '',
        'new_password': '',
        'confirm_new_password': ''
    }, follow_redirects=True)
    if res.status_code != 200 or b"Profile updated successfully" not in res.data:
        print("Profile response:", res.status_code, res.data.decode('utf-8')[:500])
    assert res.status_code == 200
    assert b"Profile updated successfully" in res.data
    print("[OK] Profile name updated successfully.")

    print("\n=======================================================")
    print(" ALL 10 END-TO-END VERIFICATION FLOWS PASSED PERFECTLY!")
    print("=======================================================\n")

if __name__ == '__main__':
    test_full_system_flow()
