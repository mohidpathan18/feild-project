"""
GLOBAL EDU - Flask Application
A comprehensive, professional, fully functional Study Abroad web platform.
Includes student portal, search & multi-filters, cost calculator, application planner,
contact forms, and complete admin CRUD management.
"""

import os
import re
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, abort, jsonify
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash

import database as db

# Load environment configuration if available
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Secret key configuration with safe development fallback
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'global-edu-dev-secret-key-2026-safe-fallback-x99')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None  # Prevent CSRF token timeout during testing

# Initialize CSRF Protection
csrf = CSRFProtect(app)


# ------------------------------------------------------------------------------
# Authentication & Role Decorators
# ------------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash("Administrator access required.", "danger")
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------------------------------------------------------
# Context Processors & Template Helpers
# ------------------------------------------------------------------------------

@app.context_processor
def inject_global_data():
    """Inject common variables into all templates."""
    current_user = None
    if 'user_id' in session:
        current_user = {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role')
        }
    return {
        'current_user': current_user,
        'app_name': 'GLOBAL EDU',
        'is_admin': session.get('role') == 'admin'
    }


# ------------------------------------------------------------------------------
# Public Routes
# ------------------------------------------------------------------------------

@app.route('/')
def index():
    """Home page with hero, statistics, featured destinations, top universities, and scholarships."""
    countries = db.get_all_countries()
    universities = db.filter_universities()[:6]
    scholarships = db.filter_scholarships()[:4]
    stats = db.get_platform_stats()
    return render_template('index.html',
                           countries=countries,
                           universities=universities,
                           scholarships=scholarships,
                           stats=stats)


@app.route('/countries')
def countries():
    """Explore Study Abroad Countries with search and overview badges."""
    search_query = request.args.get('search', '').strip()
    country_list = db.get_all_countries(search=search_query if search_query else None)
    return render_template('countries.html', countries=country_list, search=search_query)


@app.route('/countries/<slug>')
def country_detail(slug):
    """Country Details page with living expenses, tuition, top universities, and visa guidelines."""
    country = db.get_country_by_slug(slug)
    if not country:
        abort(404)
    universities = db.get_universities_by_country(country['id'])
    scholarships = db.get_scholarships_by_country(country['id'])
    return render_template('country_detail.html',
                           country=country,
                           universities=universities,
                           scholarships=scholarships)


@app.route('/universities')
def universities():
    """Universities listing with multi-facet filters: Country, Degree, Course, Tuition Range, Search."""
    country_id = request.args.get('country', type=int)
    degree = request.args.get('degree', '').strip()
    course = request.args.get('course', '').strip()
    search = request.args.get('search', '').strip()
    max_tuition = request.args.get('max_tuition', type=float)

    univ_list = db.filter_universities(
        country_id=country_id,
        degree=degree if degree else None,
        course=course if course else None,
        search=search if search else None,
        max_tuition=max_tuition
    )
    all_countries = db.get_all_countries()

    saved_ids = set()
    if 'user_id' in session:
        saved_records = db.get_saved_universities_for_user(session['user_id'])
        saved_ids = {r['id'] for r in saved_records}

    return render_template('universities.html',
                           universities=univ_list,
                           countries=all_countries,
                           selected_country=country_id,
                           selected_degree=degree,
                           selected_course=course,
                           search=search,
                           max_tuition=max_tuition,
                           saved_ids=saved_ids)


@app.route('/universities/<int:univ_id>')
def university_detail(univ_id):
    """University Details page showing degrees, courses, tuition, requirements, and official links."""
    university = db.get_university_by_id(univ_id)
    if not university:
        abort(404)

    is_saved = False
    if 'user_id' in session:
        is_saved = db.is_university_saved(session['user_id'], univ_id)

    # Get country scholarships
    scholarships = db.get_scholarships_by_country(university['country_id'])

    return render_template('university_detail.html',
                           university=university,
                           is_saved=is_saved,
                           scholarships=scholarships)


@app.route('/scholarships')
def scholarships():
    """Scholarships listing with country and coverage type filters."""
    country_id = request.args.get('country', type=int)
    coverage = request.args.get('coverage', '').strip()
    search = request.args.get('search', '').strip()

    scholarship_list = db.filter_scholarships(
        country_id=country_id,
        coverage_type=coverage if coverage else None,
        search=search if search else None
    )
    all_countries = db.get_all_countries()

    return render_template('scholarships.html',
                           scholarships=scholarship_list,
                           countries=all_countries,
                           selected_country=country_id,
                           selected_coverage=coverage,
                           search=search)


@app.route('/scholarships/<int:scholarship_id>')
def scholarship_detail(scholarship_id):
    """Detailed view for a specific scholarship."""
    scholarship = db.get_scholarship_by_id(scholarship_id)
    if not scholarship:
        abort(404)
    return render_template('scholarship_detail.html', scholarship=scholarship)


@app.route('/admissions')
def admissions():
    """Comprehensive guide to international admission requirements."""
    countries = db.get_all_countries()
    return render_template('admissions.html', countries=countries)


@app.route('/cost-calculator')
def cost_calculator():
    """Interactive Study Cost Calculator page."""
    countries = db.get_all_countries()
    return render_template('calculator.html', countries=countries)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact Us page with inquiry submission stored in SQLite."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # Input validation
        if not name or len(name) < 2:
            flash("Please enter your full name (minimum 2 characters).", "danger")
            return render_template('contact.html')

        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Please provide a valid email address.", "danger")
            return render_template('contact.html')

        if not subject or len(subject) < 3:
            flash("Please enter a subject (minimum 3 characters).", "danger")
            return render_template('contact.html')

        if not message or len(message) < 10:
            flash("Message body must be at least 10 characters long.", "danger")
            return render_template('contact.html')

        db.save_contact_message(name, email, subject, message)
        flash("Thank you! Your message has been received. Our advisors will reply shortly.", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')


# ------------------------------------------------------------------------------
# Student Authentication Routes
# ------------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student registration page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not full_name or len(full_name) < 2:
            flash("Full name must be at least 2 characters long.", "danger")
            return render_template('register.html')

        if not username or len(username) < 3 or not username.isalnum():
            flash("Username must be at least 3 alphanumeric characters.", "danger")
            return render_template('register.html')

        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Please provide a valid email address.", "danger")
            return render_template('register.html')

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        # Check existing user
        existing_user = db.get_user_by_username_or_email(username)
        if existing_user:
            flash("Username is already taken. Please choose another.", "danger")
            return render_template('register.html')

        existing_email = db.get_user_by_username_or_email(email)
        if existing_email:
            flash("Email address is already registered. Please log in.", "danger")
            return render_template('register.html')

        user_id, err = db.create_user(username, email, password, full_name, role='student')
        if err:
            flash("Registration error: could not create account.", "danger")
            return render_template('register.html')

        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Student login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template('login.html')

        user = db.get_user_by_username_or_email(identifier)
        if not user or not check_password_hash(user['password_hash'], password):
            flash("Invalid username/email or password.", "danger")
            return render_template('login.html')

        # Prevent admin login through student portal for clean role separation
        if user['role'] == 'admin':
            flash("Administrator accounts must sign in via the Admin Portal.", "info")
            return redirect(url_for('admin_login'))

        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user['role']

        flash(f"Welcome back, {user['full_name']}!", "success")
        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('index'))


# ------------------------------------------------------------------------------
# Student Portal Routes (Authenticated & User Isolated)
# ------------------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    """Student Dashboard with overview stats, applications pipeline, and saved universities."""
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    saved_universities = db.get_saved_universities_for_user(user_id)
    applications = db.get_applications_for_user(user_id)

    # Status counts
    app_stats = {
        'total': len(applications),
        'draft': sum(1 for a in applications if a['status'] == 'Draft'),
        'submitted': sum(1 for a in applications if a['status'] == 'Submitted'),
        'under_review': sum(1 for a in applications if a['status'] == 'Under Review'),
        'accepted': sum(1 for a in applications if a['status'] == 'Accepted'),
        'waitlisted': sum(1 for a in applications if a['status'] == 'Waitlisted'),
        'rejected': sum(1 for a in applications if a['status'] == 'Rejected')
    }

    return render_template('dashboard.html',
                           user=user,
                           saved_universities=saved_universities,
                           applications=applications,
                           app_stats=app_stats)


@app.route('/saved-universities')
@login_required
def saved_universities():
    """Student's saved/bookmarked universities list."""
    user_id = session['user_id']
    saved = db.get_saved_universities_for_user(user_id)
    return render_template('saved_universities.html', saved_universities=saved)


@app.route('/saved-universities/toggle/<int:univ_id>', methods=['POST'])
@login_required
def toggle_save(univ_id):
    """Toggle university saved status for current student."""
    user_id = session['user_id']
    is_saved, message = db.toggle_save_university(user_id, univ_id)
    flash(message, "success" if is_saved else "info")

    next_url = request.form.get('next') or request.referrer or url_for('saved_universities')
    return redirect(next_url)


@app.route('/applications', methods=['GET'])
@login_required
def applications():
    """Application Planner with status tracking and timeline notes."""
    user_id = session['user_id']
    app_list = db.get_applications_for_user(user_id)
    all_universities = db.filter_universities()
    return render_template('applications.html',
                           applications=app_list,
                           universities=all_universities)


@app.route('/applications/create', methods=['POST'])
@login_required
def create_application():
    """Create a new application for the logged-in student."""
    user_id = session['user_id']
    university_id = request.form.get('university_id', type=int)
    degree_level = request.form.get('degree_level', '').strip()
    program_name = request.form.get('program_name', '').strip()
    intake_year = request.form.get('intake_year', type=int)
    intake_semester = request.form.get('intake_semester', '').strip()
    status = request.form.get('status', 'Draft').strip()
    notes = request.form.get('notes', '').strip()

    if not university_id or not degree_level or not program_name or not intake_year or not intake_semester:
        flash("Please fill in all required application fields.", "danger")
        return redirect(url_for('applications'))

    db.create_application(
        user_id=user_id,
        university_id=university_id,
        degree_level=degree_level,
        program_name=program_name,
        intake_year=intake_year,
        intake_semester=intake_semester,
        status=status,
        notes=notes
    )
    flash("Application plan created successfully!", "success")
    return redirect(url_for('applications'))


@app.route('/applications/<int:app_id>/update', methods=['POST'])
@login_required
def update_application_status(app_id):
    """Update status and notes of student's own application record."""
    user_id = session['user_id']
    app_record = db.get_application_by_id_and_user(app_id, user_id)
    if not app_record:
        abort(404)

    degree_level = request.form.get('degree_level', app_record['degree_level']).strip()
    program_name = request.form.get('program_name', app_record['program_name']).strip()
    intake_year = request.form.get('intake_year', app_record['intake_year'], type=int)
    intake_semester = request.form.get('intake_semester', app_record['intake_semester']).strip()
    status = request.form.get('status', app_record['status']).strip()
    notes = request.form.get('notes', '').strip()

    updated = db.update_application(
        app_id=app_id,
        user_id=user_id,
        degree_level=degree_level,
        program_name=program_name,
        intake_year=intake_year,
        intake_semester=intake_semester,
        status=status,
        notes=notes
    )
    if updated:
        flash("Application record updated successfully.", "success")
    else:
        flash("Could not update application record.", "danger")

    return redirect(url_for('applications'))


@app.route('/applications/<int:app_id>/delete', methods=['POST'])
@login_required
def delete_application_record(app_id):
    """Delete an application record owned by student."""
    user_id = session['user_id']
    deleted = db.delete_application(app_id, user_id)
    if deleted:
        flash("Application record removed.", "info")
    else:
        flash("Could not remove record or unauthorized.", "danger")
    return redirect(url_for('applications'))


# ------------------------------------------------------------------------------
# Admin Portal Routes (Admin Role Only)
# ------------------------------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin portal login page."""
    if 'user_id' in session and session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    local_admin = db.get_admin_credentials_info()

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash("Please enter both admin username and password.", "danger")
            return render_template('admin/login.html', local_admin=local_admin)

        user = db.get_user_by_username_or_email(identifier)
        if not user or user['role'] != 'admin' or not check_password_hash(user['password_hash'], password):
            flash("Invalid administrator credentials.", "danger")
            return render_template('admin/login.html', local_admin=local_admin)

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = 'admin'

        flash(f"Logged in as Administrator: {user['username']}", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/login.html', local_admin=local_admin)


@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.clear()
    flash("Administrator logged out.", "info")
    return redirect(url_for('admin_login'))


@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Administrator overview dashboard."""
    stats = db.get_platform_stats()
    countries = db.get_all_countries()
    universities = db.filter_universities()
    scholarships = db.filter_scholarships()
    messages = db.get_all_contact_messages()
    return render_template('admin/dashboard.html',
                           stats=stats,
                           countries=countries,
                           universities=universities,
                           scholarships=scholarships,
                           messages=messages)


# --- Admin Countries CRUD ---

@app.route('/admin/countries')
@admin_required
def admin_countries():
    """Admin list countries."""
    countries_list = db.get_all_countries()
    return render_template('admin/countries.html', countries=countries_list)


@app.route('/admin/countries/add', methods=['GET', 'POST'])
@admin_required
def admin_add_country():
    """Add a new study destination country."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        capital = request.form.get('capital', '').strip()
        language = request.form.get('language', '').strip()
        currency = request.form.get('currency', '').strip()
        currency_code = request.form.get('currency_code', '').strip().upper()
        avg_tuition = request.form.get('avg_tuition_annual_usd', type=float) or 0.0
        avg_living = request.form.get('avg_living_monthly_usd', type=float) or 0.0
        overview = request.form.get('overview', '').strip()
        visa_req = request.form.get('visa_requirements', '').strip()
        work_info = request.form.get('work_permit_info', '').strip()
        cities = request.form.get('popular_cities', '').strip()

        if not name or not code or not currency_code:
            flash("Country name, 2-letter code, and currency code are required.", "danger")
            return render_template('admin/country_form.html', country=None)

        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

        try:
            db.admin_create_country(
                name=name, slug=slug, code=code, capital=capital, language=language,
                currency=currency, currency_code=currency_code,
                avg_tuition_annual_usd=avg_tuition, avg_living_monthly_usd=avg_living,
                overview=overview, visa_requirements=visa_req,
                work_permit_info=work_info, popular_cities=cities
            )
            flash(f"Country '{name}' added successfully!", "success")
            return redirect(url_for('admin_countries'))
        except Exception as e:
            flash(f"Error saving country: {e}", "danger")

    return render_template('admin/country_form.html', country=None)


@app.route('/admin/countries/<int:c_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_country(c_id):
    """Edit existing study destination country."""
    country = db.get_country_by_id(c_id)
    if not country:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        capital = request.form.get('capital', '').strip()
        language = request.form.get('language', '').strip()
        currency = request.form.get('currency', '').strip()
        currency_code = request.form.get('currency_code', '').strip().upper()
        avg_tuition = request.form.get('avg_tuition_annual_usd', type=float) or 0.0
        avg_living = request.form.get('avg_living_monthly_usd', type=float) or 0.0
        overview = request.form.get('overview', '').strip()
        visa_req = request.form.get('visa_requirements', '').strip()
        work_info = request.form.get('work_permit_info', '').strip()
        cities = request.form.get('popular_cities', '').strip()

        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

        try:
            db.admin_update_country(
                country_id=c_id, name=name, slug=slug, code=code, capital=capital,
                language=language, currency=currency, currency_code=currency_code,
                avg_tuition_annual_usd=avg_tuition, avg_living_monthly_usd=avg_living,
                overview=overview, visa_requirements=visa_req,
                work_permit_info=work_info, popular_cities=cities
            )
            flash(f"Country '{name}' updated successfully!", "success")
            return redirect(url_for('admin_countries'))
        except Exception as e:
            flash(f"Error updating country: {e}", "danger")

    return render_template('admin/country_form.html', country=country)


@app.route('/admin/countries/<int:c_id>/delete', methods=['POST'])
@admin_required
def admin_delete_country(c_id):
    """Delete country and dependent universities."""
    country = db.get_country_by_id(c_id)
    if country:
        db.admin_delete_country(c_id)
        flash(f"Country '{country['name']}' deleted.", "info")
    return redirect(url_for('admin_countries'))


# --- Admin Universities CRUD ---

@app.route('/admin/universities')
@admin_required
def admin_universities():
    """Admin list universities."""
    univ_list = db.filter_universities()
    return render_template('admin/universities.html', universities=univ_list)


@app.route('/admin/universities/add', methods=['GET', 'POST'])
@admin_required
def admin_add_university():
    """Add a new university."""
    countries = db.get_all_countries()
    if request.method == 'POST':
        country_id = request.form.get('country_id', type=int)
        name = request.form.get('name', '').strip()
        city = request.form.get('city', '').strip()
        world_ranking = request.form.get('world_ranking', type=int)
        website_url = request.form.get('website_url', '').strip()
        description = request.form.get('description', '').strip()
        degrees_offered = request.form.get('degrees_offered', '').strip()
        popular_courses = request.form.get('popular_courses', '').strip()
        avg_tuition = request.form.get('avg_tuition_usd', type=float) or 0.0
        admission_req = request.form.get('admission_requirements', '').strip()
        intake_months = request.form.get('intake_months', '').strip()

        if not country_id or not name or not website_url:
            flash("Country, university name, and official website URL are required.", "danger")
            return render_template('admin/university_form.html', university=None, countries=countries)

        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

        try:
            db.admin_create_university(
                country_id=country_id, name=name, slug=slug, city=city,
                world_ranking=world_ranking, website_url=website_url,
                description=description, degrees_offered=degrees_offered,
                popular_courses=popular_courses, avg_tuition_usd=avg_tuition,
                admission_requirements=admission_req, intake_months=intake_months
            )
            flash(f"University '{name}' added successfully!", "success")
            return redirect(url_for('admin_universities'))
        except Exception as e:
            flash(f"Error creating university: {e}", "danger")

    return render_template('admin/university_form.html', university=None, countries=countries)


@app.route('/admin/universities/<int:u_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_university(u_id):
    """Edit existing university."""
    university = db.get_university_by_id(u_id)
    if not university:
        abort(404)
    countries = db.get_all_countries()

    if request.method == 'POST':
        country_id = request.form.get('country_id', type=int)
        name = request.form.get('name', '').strip()
        city = request.form.get('city', '').strip()
        world_ranking = request.form.get('world_ranking', type=int)
        website_url = request.form.get('website_url', '').strip()
        description = request.form.get('description', '').strip()
        degrees_offered = request.form.get('degrees_offered', '').strip()
        popular_courses = request.form.get('popular_courses', '').strip()
        avg_tuition = request.form.get('avg_tuition_usd', type=float) or 0.0
        admission_req = request.form.get('admission_requirements', '').strip()
        intake_months = request.form.get('intake_months', '').strip()
        campus_image = university['campus_image'] or 'default.jpg'

        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

        try:
            db.admin_update_university(
                univ_id=u_id, country_id=country_id, name=name, slug=slug, city=city,
                world_ranking=world_ranking, website_url=website_url,
                description=description, degrees_offered=degrees_offered,
                popular_courses=popular_courses, avg_tuition_usd=avg_tuition,
                admission_requirements=admission_req, intake_months=intake_months,
                campus_image=campus_image
            )
            flash(f"University '{name}' updated successfully!", "success")
            return redirect(url_for('admin_universities'))
        except Exception as e:
            flash(f"Error updating university: {e}", "danger")

    return render_template('admin/university_form.html', university=university, countries=countries)


@app.route('/admin/universities/<int:u_id>/delete', methods=['POST'])
@admin_required
def admin_delete_university(u_id):
    """Delete university."""
    university = db.get_university_by_id(u_id)
    if university:
        db.admin_delete_university(u_id)
        flash(f"University '{university['name']}' deleted.", "info")
    return redirect(url_for('admin_universities'))


# --- Admin Scholarships CRUD ---

@app.route('/admin/scholarships')
@admin_required
def admin_scholarships():
    """Admin list scholarships."""
    scholarships_list = db.filter_scholarships()
    return render_template('admin/scholarships.html', scholarships=scholarships_list)


@app.route('/admin/scholarships/add', methods=['GET', 'POST'])
@admin_required
def admin_add_scholarship():
    """Add new scholarship."""
    countries = db.get_all_countries()
    universities = db.filter_universities()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        provider = request.form.get('provider', '').strip()
        country_id = request.form.get('country_id', type=int) or None
        university_id = request.form.get('university_id', type=int) or None
        award_amount = request.form.get('award_amount_usd', type=float) or 0.0
        coverage_type = request.form.get('coverage_type', '').strip()
        eligibility = request.form.get('eligibility_criteria', '').strip()
        deadline = request.form.get('deadline', '').strip()
        application_url = request.form.get('application_url', '').strip()
        description = request.form.get('description', '').strip()

        if not title or not provider or not application_url:
            flash("Scholarship title, provider, and application URL are required.", "danger")
            return render_template('admin/scholarship_form.html',
                                   scholarship=None, countries=countries, universities=universities)

        try:
            db.admin_create_scholarship(
                university_id=university_id, country_id=country_id,
                title=title, provider=provider, award_amount_usd=award_amount,
                coverage_type=coverage_type, eligibility_criteria=eligibility,
                deadline=deadline, application_url=application_url, description=description
            )
            flash(f"Scholarship '{title}' created successfully!", "success")
            return redirect(url_for('admin_scholarships'))
        except Exception as e:
            flash(f"Error creating scholarship: {e}", "danger")

    return render_template('admin/scholarship_form.html',
                           scholarship=None, countries=countries, universities=universities)


@app.route('/admin/scholarships/<int:s_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_scholarship(s_id):
    """Edit existing scholarship."""
    scholarship = db.get_scholarship_by_id(s_id)
    if not scholarship:
        abort(404)
    countries = db.get_all_countries()
    universities = db.filter_universities()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        provider = request.form.get('provider', '').strip()
        country_id = request.form.get('country_id', type=int) or None
        university_id = request.form.get('university_id', type=int) or None
        award_amount = request.form.get('award_amount_usd', type=float) or 0.0
        coverage_type = request.form.get('coverage_type', '').strip()
        eligibility = request.form.get('eligibility_criteria', '').strip()
        deadline = request.form.get('deadline', '').strip()
        application_url = request.form.get('application_url', '').strip()
        description = request.form.get('description', '').strip()

        try:
            db.admin_update_scholarship(
                s_id=s_id, university_id=university_id, country_id=country_id,
                title=title, provider=provider, award_amount_usd=award_amount,
                coverage_type=coverage_type, eligibility_criteria=eligibility,
                deadline=deadline, application_url=application_url, description=description
            )
            flash(f"Scholarship '{title}' updated successfully!", "success")
            return redirect(url_for('admin_scholarships'))
        except Exception as e:
            flash(f"Error updating scholarship: {e}", "danger")

    return render_template('admin/scholarship_form.html',
                           scholarship=scholarship, countries=countries, universities=universities)


@app.route('/admin/scholarships/<int:s_id>/delete', methods=['POST'])
@admin_required
def admin_delete_scholarship(s_id):
    """Delete scholarship."""
    scholarship = db.get_scholarship_by_id(s_id)
    if scholarship:
        db.admin_delete_scholarship(s_id)
        flash(f"Scholarship '{scholarship['title']}' deleted.", "info")
    return redirect(url_for('admin_scholarships'))


# --- Admin Messages Management ---

@app.route('/admin/messages')
@admin_required
def admin_messages():
    """View and manage contact form inquiries."""
    messages_list = db.get_all_contact_messages()
    return render_template('admin/messages.html', messages=messages_list)


@app.route('/admin/messages/<int:m_id>/read', methods=['POST'])
@admin_required
def admin_mark_message_read(m_id):
    """Mark a message as read."""
    db.mark_contact_message_read(m_id)
    flash("Message marked as read.", "info")
    return redirect(url_for('admin_messages'))


@app.route('/admin/messages/<int:m_id>/delete', methods=['POST'])
@admin_required
def admin_delete_message(m_id):
    """Delete a contact message."""
    db.delete_contact_message(m_id)
    flash("Message deleted.", "info")
    return redirect(url_for('admin_messages'))


# ------------------------------------------------------------------------------
# Custom Error Handlers
# ------------------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500


# ------------------------------------------------------------------------------
# Application Startup (Windows IDLE & CLI Ready)
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    # Initialize database safely on startup
    db.init_db()

    port = int(os.environ.get('PORT', 5000))
    host = "127.0.0.1"

    admin_info = db.get_admin_credentials_info()
    admin_user_display = admin_info['username'] if admin_info else os.environ.get('ADMIN_USERNAME', 'admin')
    admin_pw_display = admin_info['password'] if admin_info else "(Configured in .env)"

    print("=" * 65)
    print("  GLOBAL EDU - Study Abroad Portal")
    print(f"  Server URL: http://{host}:{port}")
    print("  Local Demo Student Account:")
    print("    Username: student")
    print("    Password: StudentPass123!")
    print("  Administrator Credentials (Local Development):")
    print(f"    Username: {admin_user_display}")
    print(f"    Password: {admin_pw_display}")
    print("    File:     instance/.admin_credentials.txt")
    print("  Windows IDLE Tip: Stop server anytime with Ctrl+C in console")
    print("=" * 65)

    # Use debug=False and use_reloader=False for flawless Windows IDLE execution
    app.run(host=host, port=port, debug=False, use_reloader=False)
