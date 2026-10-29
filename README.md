# Student Project Submission & Evaluation Management System (SPEMS)

A complete, production-ready, full-stack web application designed for higher education institutions to manage project assignments, deliverables, versioned student submissions, faculty rubrics, in-app notifications, and academic reporting.

---

## 🌟 Key Highlights & Features

### 1. Robust Role-Based Access Control (RBAC)
- **Three Distinct User Roles**: `Student`, `Faculty`, `Admin`.
- Enforced with reusable `@role_required(...)` and `@login_required` decorators.
- Unauthorized attempts cleanly display a dedicated, customized **HTTP 403 Forbidden** security page.
- Session-based authentication with Werkzeug password hashing (no plain-text passwords stored).

### 2. Student Portal
- **Self-Registration**: Name, Register Number, Department, Academic Year, Email, and Password with confirmation matching.
- **Available Assignments Feed**: Displays course assignments with live, real-time JavaScript countdown timers ticking every second.
- **Strict File Upload Validation**: Validates file extension, MIME type, and file size (Max 10 MB for PDF reports, 25 MB for ZIP source archives).
- **Automated Late Detection**: Automatically timestamps submissions against the deadline. Flags late submissions with a visible red badge. If late submissions are disabled by the instructor, the system strictly blocks the upload with a clear message.
- **Version Control & Resubmissions**: Supports iterative resubmission if faculty requests revision, preserving full submission history (v1, v2, etc.).
- **Personal Progress Tracking**: Interactive Chart.js bar graph tracking personal score percentages across completed evaluations.

### 3. Faculty Portal
- **Project Assignment Management**: Create, edit, and delete assignments with target department, academic year, maximum marks, deadline picker, optional guide attachments (PDF/ZIP/DOC), and allow-late toggle.
- **Deliverables Assessment**: Download student report PDF and source code ZIP files.
- **Evaluation Workflow**: Input marks (strictly validated against max marks), status (`Approved`, `Needs Revision`, `Rejected`), and detailed written feedback.
- **Faculty Analytics**: Real-time Chart.js charts for Pending vs. Evaluated submissions and class average marks per assignment.

### 4. Admin Portal
- **Institution-wide Metrics & Stats**: Total students, faculty, assignments, submissions, pending reviews, and late submissions.
- **4 Interactive Chart.js Visualizations**:
  1. Submissions per Assignment (Bar Chart)
  2. Submission Status Distribution (Doughnut Chart)
  3. Submission Volume Trend (Line Chart)
  4. Average Marks by Assignment (Bar Chart)
- **User Management**: Add faculty and student accounts, edit credentials, deactivate/activate accounts, reset passwords, search, and pagination.
- **Audit Logs**: Real-time activity log tracking user logins, assignment creation, student submissions, and evaluations.

### 5. Academic Reporting & Exports
- **CSV Data Export**: One-click download of all evaluation data formatted for spreadsheets (`.csv`).
- **Official Printable HTML/PDF Report**: Formatted with `@media print` styling, college letterhead, cohort statistics (highest, lowest, average marks), marks table, and signature blocks.

### 6. In-App Notification System
- Bell icon in the top navigation bar with live unread counter badge.
- Instant notifications triggered on:
  - New assignment publication (alerting students in target department/year)
  - Student project submission (alerting faculty)
  - Faculty evaluation completed (alerting student with marks and status)
  - Resubmission requested (`Needs Revision`)
  - Deadline approaching (alerts student within 24 hours of deadline)

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask (Application Factory Pattern + Blueprints)
- **Database & ORM**: SQLite, Flask-SQLAlchemy
- **Forms & CSRF Security**: Flask-WTF, WTForms, email-validator
- **Frontend & UI**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3 (CDN), Bootstrap Icons
- **Data Visualizations**: Chart.js 4 (CDN)
- **Testing**: pytest

---

## 📁 Directory Structure

```
student_project_system/
├── app/
│   ├── __init__.py               # Flask application factory, filters, error handlers
│   ├── models.py                 # SQLAlchemy database models (User, Assignment, Submission, etc.)
│   ├── extensions.py             # Extension instances (db, csrf)
│   ├── decorators.py             # Role-based access control (@role_required, @login_required)
│   ├── utils.py                  # File upload validation, notifications, late checker
│   ├── forms.py                  # Flask-WTF form classes
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── auth.py               # Login, register, profile, logout
│   │   ├── student.py            # Student dashboard, submit, history, downloads
│   │   ├── faculty.py            # Faculty dashboard, assignment CRUD, evaluations
│   │   ├── admin.py              # Admin metrics, user management, global views
│   │   ├── notifications.py      # Notification center & read endpoints
│   │   └── reports.py            # CSV export and printable evaluation reports
│   ├── templates/
│   │   ├── base.html             # Master responsive layout with role-based sidebar
│   │   ├── notifications.html    # Notification management center
│   │   ├── errors/               # Custom 403, 404, and 500 error pages
│   │   ├── auth/                 # Login, student registration, profile
│   │   ├── student/              # Student dashboard, assignment detail, history
│   │   ├── faculty/              # Faculty dashboard, assignment form, submissions, grading
│   │   ├── admin/                # Admin dashboard, user list, user form, assignments, submissions
│   │   └── reports/              # Printable academic report template
│   └── static/
│       ├── css/style.css         # Custom modern design, cards, badges
│       └── js/main.js            # Real-time countdown timers, client filters, notifications
├── uploads/
│   ├── reports/                  # Uploaded PDF project reports
│   ├── code/                     # Uploaded ZIP source archives
│   └── assignment_files/         # Faculty reference guides and attachments
├── instance/
│   └── student_system.db         # SQLite database
├── tests/
│   ├── conftest.py               # Pytest fixtures and mock file generators
│   ├── test_auth.py              # Authentication unit tests
│   ├── test_roles.py             # RBAC and 403 error tests
│   ├── test_submissions.py      # File upload validation and versioning tests
│   └── test_late_detection.py    # Deadline and late detection tests
├── config.py                     # Configuration settings (Production & Testing)
├── run.py                        # Application entrypoint
├── seed.py                       # Comprehensive database seeder (users, cohorts, submissions)
├── verify_app.py                 # Automated 10-step full workflow verification script
├── requirements.txt              # Project dependencies
└── .gitignore
```

---

## ⚡ Quick Start & Installation

### One-Command Setup & Run
From inside the `student_project_system` directory:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed database with realistic sample data and files
python seed.py

# 3. Start the Flask application
python run.py
```

Open your browser at: **`http://127.0.0.1:5000`**

---

## 🔑 Default Credentials

The `seed.py` script automatically seeds realistic sample users and past/future assignments:

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@college.edu` | `Admin@123` | Institutional Superadmin |
| **Faculty (CS)** | `sarah.faculty@college.edu` | `Faculty@123` | Prof. Sarah Connor (Computer Science) |
| **Faculty (IT)** | `alan.faculty@college.edu` | `Faculty@123` | Dr. Alan Turing (Information Technology) |
| **Faculty (EC)** | `marie.faculty@college.edu` | `Faculty@123` | Prof. Marie Curie (Electronics) |
| **Student (CS Y3)** | `alex.student@college.edu` | `Student@123` | Alex Johnson (Reg: `CS202301`) |
| **Student (IT Y3)** | `daniel.student@college.edu` | `Student@123` | Daniel Anderson (Reg: `IT202301`) |
| **All Other Students** | `<firstname>.student@college.edu` | `Student@123` | 15 pre-seeded students across departments |

> **Tip**: The login page includes convenient **One-Click Autofill Buttons** to instantly log in as Admin, Faculty, or Student for testing.

---

## 🧪 Running the Automated Test Suite

Run unit and integration tests using `pytest`:

```bash
python -m pytest -v tests/
```

Run the end-to-end integration verification script:

```bash
python verify_app.py
```

---

## 📸 Application Workflows

1. **Sign-In & Role Redirection**: Users are authenticated and automatically redirected to their specific dashboard based on their role (`/admin/dashboard`, `/faculty/dashboard`, or `/student/dashboard`).
2. **Assignment Publication**: Faculty creates an assignment, setting deadlines, maximum points, and upload permissions. Matching students are immediately notified.
3. **Project Submission**: Students upload their PDF report and ZIP codebase. If late submissions are enabled and the deadline has passed, the submission is recorded with a distinct `Late` badge.
4. **Grading & Rubrics**: Faculty reviews the deliverables, awards numerical marks, selects `Approved` / `Needs Revision` / `Rejected`, and inputs feedback.
5. **Academic Reports**: Admin and faculty can generate and export evaluation spreadsheets (`.csv`) or open print-ready letterhead reports.
