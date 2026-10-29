import pytest

def test_unauthenticated_access_redirects(client):
    res = client.get('/admin/dashboard')
    assert res.status_code == 302
    assert '/login' in res.location

def test_student_cannot_access_admin_dashboard(client, seed_users):
    client.post('/login', data={'email': 'student@test.com', 'password': 'Student@123'})
    res = client.get('/admin/dashboard')
    assert res.status_code == 403
    assert b"403" in res.data
    assert b"Access Forbidden" in res.data

def test_faculty_cannot_access_admin_dashboard(client, seed_users):
    client.post('/login', data={'email': 'faculty@test.com', 'password': 'Faculty@123'})
    res = client.get('/admin/dashboard')
    assert res.status_code == 403

def test_admin_can_access_admin_dashboard(client, seed_users):
    client.post('/login', data={'email': 'admin@test.com', 'password': 'Admin@123'})
    res = client.get('/admin/dashboard')
    assert res.status_code == 200
    assert b"Administrative Overview" in res.data

def test_student_cannot_access_faculty_routes(client, seed_users):
    client.post('/login', data={'email': 'student@test.com', 'password': 'Student@123'})
    res = client.get('/faculty/dashboard')
    assert res.status_code == 403

def test_faculty_can_access_faculty_dashboard(client, seed_users):
    client.post('/login', data={'email': 'faculty@test.com', 'password': 'Faculty@123'})
    res = client.get('/faculty/dashboard')
    assert res.status_code == 200
    assert b"Faculty Evaluation Dashboard" in res.data
