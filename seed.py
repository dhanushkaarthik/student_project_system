import os
import zipfile
import uuid
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Assignment, Submission, Evaluation, Notification, ActivityLog

app = create_app()

def create_valid_dummy_pdf(filepath, title):
    content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj
4 0 obj<</Length 60>>stream
BT /F1 18 Tf 50 700 Td ({title[:40]}) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000216 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
327
%%EOF
"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(content.encode('latin1'))

def create_valid_dummy_zip(filepath, project_name):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('main.py', f'# Project: {project_name}\n# Student project entrypoint\n\ndef main():\n    print("SPEMS Project Execution OK")\n\nif __name__ == "__main__":\n    main()\n')
        zf.writestr('README.md', f'# {project_name}\n\nAutomated project deliverables archive.\nIncludes implementation source code and module configurations.\n')
        zf.writestr('requirements.txt', 'Flask>=3.0.0\npytest>=8.0.0\n')

def seed_database():
    with app.app_context():
        print("Recreating database tables...")
        db.drop_all()
        db.create_all()
        
        now = datetime.now(timezone.utc)
        upload_dir = app.config['UPLOAD_FOLDER']
        
        # 1. Create Admin
        admin = User(
            name="College Administrator",
            email="admin@college.edu",
            role="admin",
            is_active=True
        )
        admin.set_password("Admin@123")
        db.session.add(admin)
        
        # 2. Create 3 Faculty
        f1 = User(
            name="Prof. Sarah Connor",
            email="sarah.faculty@college.edu",
            role="faculty",
            department="Computer Science",
            is_active=True
        )
        f1.set_password("Faculty@123")
        
        f2 = User(
            name="Dr. Alan Turing",
            email="alan.faculty@college.edu",
            role="faculty",
            department="Information Technology",
            is_active=True
        )
        f2.set_password("Faculty@123")
        
        f3 = User(
            name="Prof. Marie Curie",
            email="marie.faculty@college.edu",
            role="faculty",
            department="Electronics & Communication",
            is_active=True
        )
        f3.set_password("Faculty@123")
        
        db.session.add_all([f1, f2, f3])
        db.session.flush()
        
        # 3. Create 15 Students
        student_data = [
            # CS (Year 3)
            ("Alex Johnson", "alex.student@college.edu", "CS202301", "Computer Science", 3),
            ("Emily Davis", "emily.student@college.edu", "CS202302", "Computer Science", 3),
            ("Michael Brown", "michael.student@college.edu", "CS202303", "Computer Science", 3),
            ("Jessica Taylor", "jessica.student@college.edu", "CS202304", "Computer Science", 3),
            # CS (Year 4)
            ("David Wilson", "david.student@college.edu", "CS202201", "Computer Science", 4),
            ("Sophia Martinez", "sophia.student@college.edu", "CS202202", "Computer Science", 4),
            # IT (Year 3)
            ("Daniel Anderson", "daniel.student@college.edu", "IT202301", "Information Technology", 3),
            ("Olivia Thomas", "olivia.student@college.edu", "IT202302", "Information Technology", 3),
            ("James Jackson", "james.student@college.edu", "IT202303", "Information Technology", 3),
            # IT (Year 4)
            ("Ava White", "ava.student@college.edu", "IT202201", "Information Technology", 4),
            ("William Harris", "william.student@college.edu", "IT202202", "Information Technology", 4),
            # EC (Year 3)
            ("Ethan Martin", "ethan.student@college.edu", "EC202301", "Electronics & Communication", 3),
            ("Mia Thompson", "mia.student@college.edu", "EC202302", "Electronics & Communication", 3),
            ("Benjamin Garcia", "benjamin.student@college.edu", "EC202303", "Electronics & Communication", 3),
            ("Charlotte Robinson", "charlotte.student@college.edu", "EC202304", "Electronics & Communication", 3),
        ]
        
        students = []
        for name, email, regno, dept, year in student_data:
            s = User(
                name=name,
                email=email,
                register_no=regno,
                role="student",
                department=dept,
                year=year,
                is_active=True
            )
            s.set_password("Student@123")
            students.append(s)
            db.session.add(s)
            
        db.session.flush()
        
        # 4. Create 5 Assignments (Mix of past & future deadlines)
        # Sample attachment guide
        guide_pdf = os.path.join(upload_dir, 'assignment_files', 'sample_guide.pdf')
        create_valid_dummy_pdf(guide_pdf, "Assignment Official Specification")
        guide_rel_path = 'assignment_files/sample_guide.pdf'
        
        a1 = Assignment(
            title="Distributed B-Tree Indexing Engine",
            description="Design and implement a concurrent multi-threaded B-Tree indexing engine with crash recovery and ACID compliance. Deliver comprehensive architectural documentation and source code with test suites.",
            faculty_id=f1.id,
            department="Computer Science",
            year=3,
            max_marks=100.0,
            deadline=now - timedelta(days=2),  # Past deadline
            allow_late=True,
            attachment_path=guide_rel_path,
            created_at=now - timedelta(days=10)
        )
        
        a2 = Assignment(
            title="Microservices Cloud API Architecture",
            description="Build a containerized microservices suite featuring API Gateway routing, OAuth2 token authentication, and asynchronous RabbitMQ event bus processing.",
            faculty_id=f1.id,
            department="Computer Science",
            year=4,
            max_marks=100.0,
            deadline=now + timedelta(hours=18),  # Within 24 hours -> triggers deadline approaching notification!
            allow_late=True,
            attachment_path=guide_rel_path,
            created_at=now - timedelta(days=5)
        )
        
        a3 = Assignment(
            title="High-Throughput Network Packet Analyzer",
            description="Develop a network packet inspection utility utilizing socket programming to inspect TCP/UDP payloads, detect port scans, and log anomalous network events.",
            faculty_id=f2.id,
            department="Information Technology",
            year=3,
            max_marks=100.0,
            deadline=now - timedelta(days=4),  # Past deadline
            allow_late=False,  # Disallows late
            attachment_path=guide_rel_path,
            created_at=now - timedelta(days=14)
        )
        
        a4 = Assignment(
            title="Embedded IoT Environmental Sensor Telemetry",
            description="Implement an embedded microcontroller telemetry gateway that measures humidity, temperature, and air quality index, broadcasting readings over MQTT to a centralized dashboard.",
            faculty_id=f3.id,
            department="Electronics & Communication",
            year=3,
            max_marks=100.0,
            deadline=now + timedelta(days=6),  # Future deadline (6 days)
            allow_late=True,
            attachment_path=guide_rel_path,
            created_at=now - timedelta(days=3)
        )
        
        a5 = Assignment(
            title="Full-Stack Web Real-Time Collaboration Engine",
            description="Create an interactive collaborative canvas whiteboard with WebSockets, room management, real-time cursor tracking, and state synchronization.",
            faculty_id=f1.id,
            department="Computer Science",
            year=3,
            max_marks=50.0,
            deadline=now - timedelta(days=1),  # Past deadline
            allow_late=True,
            attachment_path=guide_rel_path,
            created_at=now - timedelta(days=7)
        )
        
        assignments = [a1, a2, a3, a4, a5]
        db.session.add_all(assignments)
        db.session.flush()
        
        # 5. Create Submissions & Evaluations with physical dummy PDF and ZIP files
        # Student 0 (Alex Johnson) - CS Y3 -> Submits to a1 (v1 evaluated with Needs Revision, v2 evaluated Approved!)
        alex = students[0]
        
        # Alex v1
        pdf_v1 = os.path.join(upload_dir, 'reports', f"{uuid.uuid4().hex}_alex_btree_v1.pdf")
        zip_v1 = os.path.join(upload_dir, 'code', f"{uuid.uuid4().hex}_alex_btree_v1.zip")
        create_valid_dummy_pdf(pdf_v1, "Alex Johnson B-Tree Report v1")
        create_valid_dummy_zip(zip_v1, "alex_btree_v1")
        
        sub_alex_v1 = Submission(
            assignment_id=a1.id,
            student_id=alex.id,
            version=1,
            report_path=os.path.relpath(pdf_v1, upload_dir).replace('\\', '/'),
            code_path=os.path.relpath(zip_v1, upload_dir).replace('\\', '/'),
            remarks="Initial version submitted on time.",
            submitted_at=a1.deadline - timedelta(hours=12),
            is_late=False,
            status='Needs Revision',
            is_latest=False
        )
        db.session.add(sub_alex_v1)
        db.session.flush()
        
        eval_alex_v1 = Evaluation(
            submission_id=sub_alex_v1.id,
            faculty_id=f1.id,
            marks=68.0,
            feedback="Good foundation, but concurrency locks suffer from race conditions in leaf split operations. Please revise thread safety and resubmit.",
            evaluated_at=a1.deadline - timedelta(hours=2)
        )
        db.session.add(eval_alex_v1)
        
        # Alex v2 (Resubmission after deadline -> late)
        pdf_v2 = os.path.join(upload_dir, 'reports', f"{uuid.uuid4().hex}_alex_btree_v2.pdf")
        zip_v2 = os.path.join(upload_dir, 'code', f"{uuid.uuid4().hex}_alex_btree_v2.zip")
        create_valid_dummy_pdf(pdf_v2, "Alex Johnson B-Tree Report v2")
        create_valid_dummy_zip(zip_v2, "alex_btree_v2")
        
        sub_alex_v2 = Submission(
            assignment_id=a1.id,
            student_id=alex.id,
            version=2,
            report_path=os.path.relpath(pdf_v2, upload_dir).replace('\\', '/'),
            code_path=os.path.relpath(zip_v2, upload_dir).replace('\\', '/'),
            remarks="Fixed concurrency locking with read-write mutex locks.",
            submitted_at=a1.deadline + timedelta(hours=6),
            is_late=True,
            status='Approved',
            is_latest=True
        )
        db.session.add(sub_alex_v2)
        db.session.flush()
        
        eval_alex_v2 = Evaluation(
            submission_id=sub_alex_v2.id,
            faculty_id=f1.id,
            marks=92.5,
            feedback="Outstanding revision! The rwlock implementation effectively eliminates contention during concurrent search operations.",
            evaluated_at=a1.deadline + timedelta(hours=10)
        )
        db.session.add(eval_alex_v2)
        
        # Student 1 (Emily Davis) - CS Y3 -> Submits to a1 (On-time, Approved)
        emily = students[1]
        pdf_em = os.path.join(upload_dir, 'reports', f"{uuid.uuid4().hex}_emily_btree.pdf")
        zip_em = os.path.join(upload_dir, 'code', f"{uuid.uuid4().hex}_emily_btree.zip")
        create_valid_dummy_pdf(pdf_em, "Emily Davis B-Tree Report")
        create_valid_dummy_zip(zip_em, "emily_btree")
        
        sub_emily = Submission(
            assignment_id=a1.id,
            student_id=emily.id,
            version=1,
            report_path=os.path.relpath(pdf_em, upload_dir).replace('\\', '/'),
            code_path=os.path.relpath(zip_em, upload_dir).replace('\\', '/'),
            remarks="Complete implementation with 98% test coverage.",
            submitted_at=a1.deadline - timedelta(hours=8),
            is_late=False,
            status='Approved',
            is_latest=True
        )
        db.session.add(sub_emily)
        db.session.flush()
        
        eval_emily = Evaluation(
            submission_id=sub_emily.id,
            faculty_id=f1.id,
            marks=96.0,
            feedback="Exemplary work! Clean code structure, thorough benchmark charts, and elegant persistence routines.",
            evaluated_at=a1.deadline - timedelta(hours=1)
        )
        db.session.add(eval_emily)
        
        # Student 2 (Michael Brown) - CS Y3 -> Submits to a1 (Under Review)
        michael = students[2]
        pdf_mb = os.path.join(upload_dir, 'reports', f"{uuid.uuid4().hex}_michael_btree.pdf")
        zip_mb = os.path.join(upload_dir, 'code', f"{uuid.uuid4().hex}_michael_btree.zip")
        create_valid_dummy_pdf(pdf_mb, "Michael Brown B-Tree Report")
        create_valid_dummy_zip(zip_mb, "michael_btree")
        
        sub_mb = Submission(
            assignment_id=a1.id,
            student_id=michael.id,
            version=1,
            report_path=os.path.relpath(pdf_mb, upload_dir).replace('\\', '/'),
            code_path=os.path.relpath(zip_mb, upload_dir).replace('\\', '/'),
            remarks="Submitted on time.",
            submitted_at=a1.deadline - timedelta(hours=3),
            is_late=False,
            status='Under Review',
            is_latest=True
        )
        db.session.add(sub_mb)
        
        # Student 3 (Jessica Taylor) - CS Y3 -> Submits to a1 (Submitted, Late)
        jessica = students[3]
        pdf_jt = os.path.join(upload_dir, 'reports', f"{uuid.uuid4().hex}_jessica_btree.pdf")
        zip_jt = os.path.join(upload_dir, 'code', f"{uuid.uuid4().hex}_jessica_btree.zip")
        create_valid_dummy_pdf(pdf_jt, "Jessica Taylor B-Tree Report")
        create_valid_dummy_zip(zip_jt, "jessica_btree")
        
        sub_jt = Submission(
            assignment_id=a1.id,
            student_id=jessica.id,
            version=1,
            report_path=os.path.relpath(pdf_jt, upload_dir).replace('\\', '/'),
            code_path=os.path.relpath(zip_jt, upload_dir).replace('\\', '/'),
            remarks="Submitted late due to hardware diagnostics.",
            submitted_at=a1.deadline + timedelta(hours=14),
            is_late=True,
            status='Submitted',
            is_latest=True
        )
        db.session.add(sub_jt)
        
        # CS Y3 submissions to a5 (Real-time whiteboard)
        # Alex submitted to a5 (Approved)
        pdf_a5_alex = os.path.join(upload_dir, 'reports', f"{uuid.uuid4().hex}_alex_whiteboard.pdf")
        zip_a5_alex = os.path.join(upload_dir, 'code', f"{uuid.uuid4().hex}_alex_whiteboard.zip")
        create_valid_dummy_pdf(pdf_a5_alex, "Alex Johnson Whiteboard Report")
        create_valid_dummy_zip(zip_a5_alex, "alex_whiteboard")
        
        sub_a5_alex = Submission(
            assignment_id=a5.id,
            student_id=alex.id,
            version=1,
            report_path=os.path.relpath(pdf_a5_alex, upload_dir).replace('\\', '/'),
            code_path=os.path.relpath(zip_a5_alex, upload_dir).replace('\\', '/'),
            remarks="Canvas rendering with WebSocket broadcast.",
            submitted_at=a5.deadline - timedelta(hours=5),
            is_late=False,
            status='Approved',
            is_latest=True
        )
        db.session.add(sub_a5_alex)
        db.session.flush()
        
        eval_a5_alex = Evaluation(
            submission_id=sub_a5_alex.id,
            faculty_id=f1.id,
            marks=46.5,
            feedback="Smooth canvas performance. Good socket disconnect handling.",
            evaluated_at=a5.deadline - timedelta(hours=1)
        )
        db.session.add(eval_a5_alex)
        
        # IT Student (Daniel Anderson) -> Submits to a3 (Packet Analyzer)
        daniel = students[6]
        pdf_dan = os.path.join(upload_dir, 'reports', f"{uuid.uuid4().hex}_dan_packet.pdf")
        zip_dan = os.path.join(upload_dir, 'code', f"{uuid.uuid4().hex}_dan_packet.zip")
        create_valid_dummy_pdf(pdf_dan, "Daniel Anderson Packet Analyzer")
        create_valid_dummy_zip(zip_dan, "dan_packet")
        
        sub_dan = Submission(
            assignment_id=a3.id,
            student_id=daniel.id,
            version=1,
            report_path=os.path.relpath(pdf_dan, upload_dir).replace('\\', '/'),
            code_path=os.path.relpath(zip_dan, upload_dir).replace('\\', '/'),
            remarks="Socket sniffing implemented with raw AF_INET sockets.",
            submitted_at=a3.deadline - timedelta(days=1),
            is_late=False,
            status='Approved',
            is_latest=True
        )
        db.session.add(sub_dan)
        db.session.flush()
        
        eval_dan = Evaluation(
            submission_id=sub_dan.id,
            faculty_id=f2.id,
            marks=88.0,
            feedback="Impressive packet header parser. Clean separation between analyzer and terminal UI.",
            evaluated_at=a3.deadline - timedelta(hours=12)
        )
        db.session.add(eval_dan)
        
        # IT Student (Olivia Thomas) -> Submits to a3 (Needs Revision)
        olivia = students[7]
        pdf_ol = os.path.join(upload_dir, 'reports', f"{uuid.uuid4().hex}_olivia_packet.pdf")
        zip_ol = os.path.join(upload_dir, 'code', f"{uuid.uuid4().hex}_olivia_packet.zip")
        create_valid_dummy_pdf(pdf_ol, "Olivia Thomas Packet Analyzer")
        create_valid_dummy_zip(zip_ol, "olivia_packet")
        
        sub_ol = Submission(
            assignment_id=a3.id,
            student_id=olivia.id,
            version=1,
            report_path=os.path.relpath(pdf_ol, upload_dir).replace('\\', '/'),
            code_path=os.path.relpath(zip_ol, upload_dir).replace('\\', '/'),
            remarks="Packet parsing works on Linux.",
            submitted_at=a3.deadline - timedelta(hours=6),
            is_late=False,
            status='Needs Revision',
            is_latest=True
        )
        db.session.add(sub_ol)
        db.session.flush()
        
        eval_ol = Evaluation(
            submission_id=sub_ol.id,
            faculty_id=f2.id,
            marks=58.0,
            feedback="Protocol checksum calculation is erroneous for UDP packets. Please fix checksum verification and resubmit.",
            evaluated_at=a3.deadline - timedelta(hours=2)
        )
        db.session.add(eval_ol)
        
        # CS Year 4 (David Wilson) -> Submits to a2
        david = students[4]
        pdf_dw = os.path.join(upload_dir, 'reports', f"{uuid.uuid4().hex}_david_microservices.pdf")
        zip_dw = os.path.join(upload_dir, 'code', f"{uuid.uuid4().hex}_david_microservices.zip")
        create_valid_dummy_pdf(pdf_dw, "David Wilson Microservices Report")
        create_valid_dummy_zip(zip_dw, "david_microservices")
        
        sub_dw = Submission(
            assignment_id=a2.id,
            student_id=david.id,
            version=1,
            report_path=os.path.relpath(pdf_dw, upload_dir).replace('\\', '/'),
            code_path=os.path.relpath(zip_dw, upload_dir).replace('\\', '/'),
            remarks="Docker compose up starts all 4 services.",
            submitted_at=now - timedelta(hours=4),
            is_late=False,
            status='Submitted',
            is_latest=True
        )
        db.session.add(sub_dw)
        
        # 6. Seed Sample Notifications
        notifs = [
            Notification(
                user_id=alex.id,
                message="Your submission for 'Distributed B-Tree Indexing Engine' was evaluated. Marks: 92.5/100.0 (Approved).",
                link=f"/student/assignments/{a1.id}",
                is_read=False,
                created_at=now - timedelta(hours=5)
            ),
            Notification(
                user_id=alex.id,
                message=f"Reminder: Assignment '{a2.title}' is due in less than 24 hours!",
                link=f"/student/assignments/{a2.id}",
                is_read=False,
                created_at=now - timedelta(hours=2)
            ),
            Notification(
                user_id=f1.id,
                message=f"Jessica Taylor submitted assignment '{a1.title}' (v1) [LATE].",
                link=f"/faculty/assignments/{a1.id}/submissions",
                is_read=False,
                created_at=now - timedelta(hours=8)
            ),
            Notification(
                user_id=f1.id,
                message=f"David Wilson submitted assignment '{a2.title}' (v1).",
                link=f"/faculty/assignments/{a2.id}/submissions",
                is_read=False,
                created_at=now - timedelta(hours=4)
            ),
        ]
        db.session.add_all(notifs)
        
        # 7. Seed Sample Activity Logs
        logs = [
            ActivityLog(user_id=admin.id, action="System Initialized", details="Database seeded with cohorts and course rubrics", created_at=now - timedelta(days=10)),
            ActivityLog(user_id=f1.id, action="Create Assignment", details=f"Created '{a1.title}' for Computer Science Y3", created_at=now - timedelta(days=10)),
            ActivityLog(user_id=f1.id, action="Create Assignment", details=f"Created '{a2.title}' for Computer Science Y4", created_at=now - timedelta(days=5)),
            ActivityLog(user_id=alex.id, action="Project Submission", details=f"Submitted v1 for '{a1.title}'", created_at=a1.deadline - timedelta(hours=12)),
            ActivityLog(user_id=f1.id, action="Evaluate Submission", details=f"Evaluated Alex Johnson - Marks: 68.0/100.0, Status: Needs Revision", created_at=a1.deadline - timedelta(hours=2)),
            ActivityLog(user_id=alex.id, action="Project Submission", details=f"Submitted v2 for '{a1.title}'. Late: True", created_at=a1.deadline + timedelta(hours=6)),
            ActivityLog(user_id=f1.id, action="Evaluate Submission", details=f"Evaluated Alex Johnson - Marks: 92.5/100.0, Status: Approved", created_at=a1.deadline + timedelta(hours=10)),
            ActivityLog(user_id=david.id, action="Project Submission", details=f"Submitted v1 for '{a2.title}'. Late: False", created_at=now - timedelta(hours=4))
        ]
        db.session.add_all(logs)
        
        db.session.commit()
        print("Database seeded successfully with users, cohorts, assignments, submissions, and evaluations!")

if __name__ == '__main__':
    seed_database()
