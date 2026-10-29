import pytest
import os
import io
import zipfile
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Assignment, Submission
from config import TestingConfig

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def seed_users(app):
    with app.app_context():
        admin = User(name="Admin User", email="admin@test.com", role="admin", is_active=True)
        admin.set_password("Admin@123")
        
        faculty = User(name="Faculty User", email="faculty@test.com", role="faculty", department="Computer Science", is_active=True)
        faculty.set_password("Faculty@123")
        
        student = User(name="Student User", email="student@test.com", role="student", department="Computer Science", year=3, register_no="TEST001", is_active=True)
        student.set_password("Student@123")
        
        inactive = User(name="Inactive User", email="inactive@test.com", role="student", is_active=False)
        inactive.set_password("Student@123")
        
        db.session.add_all([admin, faculty, student, inactive])
        db.session.commit()
        
        return {
            'admin_id': admin.id,
            'faculty_id': faculty.id,
            'student_id': student.id,
            'inactive_id': inactive.id
        }

def make_dummy_pdf_bytes():
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj\n4 0 obj<</Length 10>>stream\nBT ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000216 00000 n \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n277\n%%EOF\n"

def make_dummy_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('main.py', 'print("hello test")\n')
    return buf.getvalue()
