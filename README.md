# GLOBAL EDU - Study Abroad Web Platform

GLOBAL EDU is a complete, modern, fully functional study abroad portal built from scratch with Python Flask, SQLite3, HTML5, CSS3, vanilla JavaScript, and Bootstrap 5. It empowers prospective international students to explore top destinations, compare universities and degree programs, discover high-value scholarships, calculate comprehensive tuition and living expenses, and track application milestones.

---

## Key Features

- **Explore Countries**: Compare destinations (Germany, Canada, Australia, UK, USA) with living expenses, tuition benchmarks, student visa requirements, and post-study work rights.
- **University Directory & Multi-Facet Filters**: Filter institutions by destination country, degree level (Bachelor's, Master's, PhD), study discipline (Computer Science, Business, Engineering, etc.), and maximum tuition.
- **Scholarship Directory**: Fully funded government programs and university entrance awards with coverage details, eligibility criteria, and deadlines.
- **Admissions Requirements Guide**: In-depth guidance covering GPA equivalencies, IELTS/TOEFL requirements, GRE/GMAT score targets, statements of purpose (SOP), and country intake cycles.
- **Dynamic Cost of Living Calculator**: Real-time calculations of tuition, accommodation tiers (dorm, shared flat, studio), lifestyle spending, and multi-currency conversions (USD, EUR, GBP, CAD, AUD) with copyable summary exports.
- **Student Authentication & Portal**: Secure registration, login, session management, and password hashing (`werkzeug.security`).
- **Saved Universities (Bookmarks)**: Students can bookmark target universities and access them directly from their dashboard.
- **Application Planner**: Milestone tracking for admissions (Draft, Submitted, Under Review, Accepted, Waitlisted, Rejected) with personal notes and strict user-level data isolation.
- **Contact Advisory**: Student inquiry submissions saved to SQLite with instant admin review.
- **Administrator Control Center**: Full CRUD management for countries, universities, scholarships, and contact messages, protected by admin-only role decorators.
- **Windows IDLE & CLI Ready**: Configured specifically to avoid Python IDLE subprocess conflicts (`debug=False`, `use_reloader=False`).

---

## Technology Stack

- **Backend**: Python 3 (3.10+ recommended, tested on Python 3.14)
- **Web Framework**: Flask 3.x
- **Database**: SQLite3 (using Python's built-in `sqlite3` module)
- **Form Security**: Flask-WTF CSRF Protection
- **Frontend**: HTML5, CSS3 (Custom Navy & Teal Design System), vanilla JavaScript, and local Bootstrap 5.3 (no Node.js or React required)
- **APIs**: Zero paid external API dependencies; 100% self-contained and local.

---

## Directory Structure

```text
global_edu/
├── app.py                     # Primary Flask server application and routes
├── database.py                # Database connection, migrations, seed data, and query helpers
├── requirements.txt           # Python dependency specification
├── .env.example               # Environment variables configuration template
├── README.md                  # Complete setup, execution, and troubleshooting guide
├── tests/
│   ├── __init__.py
│   └── test_app.py            # Automated test suite (18 test cases)
├── static/
│   ├── css/
│   │   ├── bootstrap.min.css  # Local Bootstrap 5.3 stylesheet
│   │   └── style.css          # Custom styling (Navy-blue, white, and teal theme)
│   ├── js/
│   │   ├── bootstrap.bundle.min.js # Local Bootstrap bundle with Popper
│   │   ├── main.js            # General UI interactions and alerts
│   │   └── calculator.js      # Dynamic study cost calculation logic
│   └── images/
│       └── flags/             # Standalone vector SVG flags (DE, CA, AU, GB, US)
└── instance/
    ├── global_edu.db          # SQLite3 database (auto-created on startup)
    └── .admin_credentials.txt # Generated development credentials for the admin
```

---

## Installation & Setup on Windows

### 1. Prerequisites
Ensure Python is installed on your Windows system and added to your `PATH`. Verify in PowerShell or Command Prompt:
```powershell
py --version
```

### 2. Navigate to Project Directory
```powershell
cd C:\Users\ADMIN\.gemini\antigravity\scratch\global_edu
```

### 3. Install Dependencies
Run the standard Windows pip command:
```powershell
py -m pip install -r requirements.txt
```
*(Dependencies: `Flask`, `Flask-WTF`, `python-dotenv`, `wtforms`)*

---

## Running the Website

### Method A: Running in Python IDLE (Recommended for IDLE Users)
1. Open **Python IDLE** from the Windows Start menu.
2. In IDLE, click **File** &rarr; **Open...** (or press `Ctrl+O`).
3. Browse to `C:\Users\ADMIN\.gemini\antigravity\scratch\global_edu\` and select **`app.py`**.
4. Press **`F5`** (or select **Run** &rarr; **Run Module**).
5. The IDLE Python Shell will display the startup banner:
   ```text
   =================================================================
     GLOBAL EDU - Study Abroad Portal
     Server URL: http://127.0.0.1:5000
     Local Demo Student Account:
       Username: student
       Password: StudentPass123!
     Administrator Credentials:
       See instance/.admin_credentials.txt or configured .env
   =================================================================
   ```
6. Open your web browser and go to:
   **[http://127.0.0.1:5000](http://127.0.0.1:5000)**
7. Keep the IDLE shell open while browsing. To stop the server, press `Ctrl+C` in the IDLE shell or close the shell window.

> **Why this works seamlessly in IDLE:** The server is configured with `debug=False` and `use_reloader=False`. This prevents the Werkzeug debug reloader from spawning duplicate background threads that frequently cause IDLE to freeze or lock sockets.

---

### Method B: Running via Windows PowerShell or Command Prompt
Open PowerShell in the project directory and execute:
```powershell
py app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## Default Login Credentials

### 1. Sample Student Account (Pre-configured for local testing)
- **Role:** Student
- **Username:** `student`
- **Email:** `student@example.com`
- **Password:** `StudentPass123!`
- **Access:** Student Portal at `/login`, Student Dashboard at `/dashboard`, Saved Universities at `/saved-universities`, Application Planner at `/applications`.

### 2. Administrator Account
- **Role:** Administrator
- **Portal URL:** `http://127.0.0.1:5000/admin/login`
- **Username:** `admin`
- **Current Development Password:** `AdminPass2026!`
- **Credentials Location:** Saved in `instance/.admin_credentials.txt` (and also displayed right on the `/admin/login` page for easy local testing).
- **Admin Management Utility:** You can view or change the admin password at any time via the included CLI utility:
  ```powershell
  py set_admin.py                     # View current admin info
  py set_admin.py <your_new_password> # Set a custom password
  ```
- You can also configure admin credentials in a `.env` file (copied from `.env.example`):
  ```ini
  ADMIN_USERNAME=admin
  ADMIN_PASSWORD=MySecureAdminPassword123!
  ```

---

## Running the Automated Test Suite

A comprehensive 18-case test suite tests database initialization, authentication, CSRF enforcement, user isolation, search filtering, cost calculation, and admin CRUD:

```powershell
py -m unittest discover tests -v
```

All 18 tests will execute and confirm `OK`.

---

## Troubleshooting Guide

### 1. Port 5000 Already in Use (`OSError: [Errno 10048] address already in use`)
If another service or background process is using port 5000:
1. Open PowerShell and identify which process is listening on port 5000:
   ```powershell
   netstat -ano | findstr :5000
   ```
2. You can either terminate that process or easily run GLOBAL EDU on another port:
   - **Option 1 (Command Line):** Set the `PORT` environment variable before launching:
     ```powershell
     $env:PORT="5001"
     py app.py
     ```
   - **Option 2 (.env file):** Copy `.env.example` to `.env` and set:
     ```ini
     PORT=5001
     ```
   - Then open `http://127.0.0.1:5001` in your browser.

### 2. `ERR_CONNECTION_REFUSED` in Web Browser
- Confirm that `app.py` is actively running in your Python IDLE shell or PowerShell terminal.
- Ensure you are navigating to `http://127.0.0.1:5000` (or `http://localhost:5000`) and NOT `https://` (the local dev server uses standard HTTP).
- Check that your Windows Firewall or third-party antivirus is not blocking loopback connections on 127.0.0.1.

### 3. Database Locks or Re-initialization
- If you ever need to reset the database to fresh factory sample data:
  1. Stop the running Flask server (`Ctrl+C`).
  2. Delete or rename `instance/global_edu.db`.
  3. Start `app.py` again. The application will automatically recreate all tables and re-seed all illustrative countries, universities, and scholarships.
