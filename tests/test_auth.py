import pytest
from app.models import User

def test_student_registration(client, app):
    res = client.post('/register', data={
        'name': 'New Student',
        'register_no': 'REG999',
        'email': 'newstudent@college.edu',
        'department': 'Computer Science',
        'year': 3,
        'password': 'Password@123',
        'confirm_password': 'Password@123'
    }, follow_redirects=True)
    
    assert res.status_code == 200
    assert b"Registration successful" in res.data
    
    with app.app_context():
        user = User.query.filter_by(email='newstudent@college.edu').first()
        assert user is not None
        assert user.role == 'student'
        assert user.check_password('Password@123')

def test_login_success(client, seed_users):
    res = client.post('/login', data={
        'email': 'admin@test.com',
        'password': 'Admin@123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Welcome back" in res.data

def test_login_invalid_password(client, seed_users):
    res = client.post('/login', data={
        'email': 'admin@test.com',
        'password': 'WrongPassword'
    }, follow_redirects=True)
    assert b"Invalid email or password" in res.data

def test_login_inactive_user(client, seed_users):
    res = client.post('/login', data={
        'email': 'inactive@test.com',
        'password': 'Student@123'
    }, follow_redirects=True)
    assert b"account has been deactivated" in res.data

def test_logout(client, seed_users):
    client.post('/login', data={'email': 'student@test.com', 'password': 'Student@123'})
    res = client.get('/logout', follow_redirects=True)
    assert b"logged out successfully" in res.data
