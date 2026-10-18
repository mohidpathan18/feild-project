"""
GLOBAL EDU - Database Management Module
Uses Python's built-in sqlite3 module with parameterization, foreign keys,
safe migration/initialization, and clear illustrative seed data.
"""

import os
import sqlite3
import secrets
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DEFAULT_DB_PATH = os.path.join(INSTANCE_DIR, 'global_edu.db')


def get_db_path():
    """Retrieve database file path from environment, serverless /tmp, or default instance location."""
    db_env = os.environ.get('DATABASE_PATH')
    if db_env:
        if os.path.isabs(db_env):
            return db_env
        return os.path.join(BASE_DIR, db_env)

    # Netlify and AWS Lambda serverless read-only filesystem handling
    if os.environ.get('NETLIFY') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        tmp_db = '/tmp/global_edu.db'
        if not os.path.exists(tmp_db) and os.path.exists(DEFAULT_DB_PATH):
            import shutil
            try:
                shutil.copy2(DEFAULT_DB_PATH, tmp_db)
            except Exception:
                pass
        return tmp_db

    return DEFAULT_DB_PATH


def get_db():
    """Establish and return a thread-safe connection to the SQLite database."""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(seed=True):
    """Create all required database tables and optionally seed illustrative data."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Countries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        code TEXT NOT NULL,
        capital TEXT NOT NULL,
        language TEXT NOT NULL,
        currency TEXT NOT NULL,
        currency_code TEXT NOT NULL,
        avg_tuition_annual_usd REAL NOT NULL,
        avg_living_monthly_usd REAL NOT NULL,
        overview TEXT NOT NULL,
        visa_requirements TEXT NOT NULL,
        work_permit_info TEXT NOT NULL,
        popular_cities TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Universities table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS universities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        city TEXT NOT NULL,
        world_ranking INTEGER,
        website_url TEXT NOT NULL,
        description TEXT NOT NULL,
        degrees_offered TEXT NOT NULL,
        popular_courses TEXT NOT NULL,
        avg_tuition_usd REAL NOT NULL,
        admission_requirements TEXT NOT NULL,
        intake_months TEXT NOT NULL,
        campus_image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries (id) ON DELETE CASCADE
    );
    """)

    # 4. Scholarships table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scholarships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        university_id INTEGER,
        country_id INTEGER,
        title TEXT NOT NULL,
        provider TEXT NOT NULL,
        award_amount_usd REAL NOT NULL,
        coverage_type TEXT NOT NULL,
        eligibility_criteria TEXT NOT NULL,
        deadline TEXT NOT NULL,
        application_url TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (university_id) REFERENCES universities (id) ON DELETE SET NULL,
        FOREIGN KEY (country_id) REFERENCES countries (id) ON DELETE SET NULL
    );
    """)

    # 5. Saved Universities (student bookmarks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_universities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        university_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, university_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (university_id) REFERENCES universities (id) ON DELETE CASCADE
    );
    """)

    # 6. Applications (student application planner)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        university_id INTEGER NOT NULL,
        degree_level TEXT NOT NULL,
        program_name TEXT NOT NULL,
        intake_year INTEGER NOT NULL,
        intake_semester TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Draft',
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (university_id) REFERENCES universities (id) ON DELETE CASCADE
    );
    """)

    # 7. Contact Messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    if seed:
        seed_sample_data(conn)

    conn.close()


def seed_sample_data(conn):
    """Seed clearly labelled illustrative sample records for countries, universities, scholarships, and demo users."""
    cursor = conn.cursor()

    # Check if countries already exist
    cursor.execute("SELECT COUNT(*) FROM countries")
    if cursor.fetchone()[0] == 0:
        countries = [
            (
                "Germany", "germany", "DE", "Berlin", "German (English widely spoken in academia)",
                "Euro", "EUR", 1200.0, 950.0,
                "Germany is renowned for tuition-free or very low tuition at public universities, world-class engineering, cutting-edge research facilities, and strong industry linkages across Europe.",
                "Schengen Student Visa, proof of financial resources (Blocked Account ~€11,208/year), health insurance, recognized higher education entrance qualification (Abitur equivalent or Studienkolleg).",
                "Students can work up to 140 full days or 280 half days per year. Graduates are eligible for an 18-month job seeker residence permit.",
                "Munich, Berlin, Aachen, Heidelberg, Frankfurt"
            ),
            (
                "Canada", "canada", "CA", "Ottawa", "English and French",
                "Canadian Dollar", "CAD", 24000.0, 1350.0,
                "Canada is one of the world's most welcoming study destinations, famous for academic prestige, diverse multicultural campuses, vibrant student cities, and flexible post-graduation pathways.",
                "Canadian Study Permit, Provincial Attestation Letter (PAL), letter of acceptance from a Designated Learning Institution (DLI), proof of funds ($20,635+ first year tuition), biometrics.",
                "Eligible for 20-24 hours/week on/off-campus work during study terms. Eligible for up to a 3-year Post-Graduation Work Permit (PGWP).",
                "Toronto, Vancouver, Montreal, Ottawa, Waterloo"
            ),
            (
                "Australia", "australia", "AU", "Canberra", "English",
                "Australian Dollar", "AUD", 28000.0, 1600.0,
                "Australia boasts several of the top 50 global universities, outstanding scientific research output, high standard of living, and breathtaking coastal lifestyles for international students.",
                "Student Visa (Subclass 500), Confirmation of Enrolment (CoE), Genuine Student (GS) assessment, Overseas Student Health Cover (OSHC), financial capacity verification (AUD $29,710/year).",
                "Fortnightly work rights of up to 48 hours during semesters; unlimited hours during semester breaks. Temporary Graduate Visa (subclass 485) available upon graduation.",
                "Melbourne, Sydney, Brisbane, Perth, Adelaide"
            ),
            (
                "United Kingdom", "united-kingdom", "GB", "London", "English",
                "British Pound", "GBP", 26000.0, 1500.0,
                "The UK offers historic academic tradition, intensive 1-year Master's programs, globally recognized qualifications, and direct connections to European financial and tech hubs.",
                "Student Visa (Points-Based System), Confirmation of Acceptance for Studies (CAS), proof of English proficiency (IELTS/PTE), Immigration Health Surcharge (IHS), financial maintenance proof.",
                "Up to 20 hours per week during term time for degree-level courses. UK Graduate Route allows 2 years (3 years for PhD) to work without sponsorship after graduation.",
                "London, Oxford, Cambridge, Edinburgh, Manchester"
            ),
            (
                "United States", "united-states", "US", "Washington, D.C.", "English",
                "US Dollar", "USD", 35000.0, 1800.0,
                "The United States hosts the greatest concentration of world-leading research universities, offering unmatched campus resources, interdisciplinary flexibility, and Silicon Valley career launchpads.",
                "F-1 Student Visa, Form I-20 issued by SEVP-certified institution, SEVIS I-901 fee payment, embassy interview, evidence of sufficient financial support for at least the first academic year.",
                "On-campus work allowed up to 20 hours/week during term. Curricular Practical Training (CPT) and Optional Practical Training (OPT) for 12 months (plus 24-month STEM extension).",
                "Boston/Cambridge, New York City, San Francisco Bay Area, Chicago, Austin"
            )
        ]
        cursor.executemany("""
        INSERT INTO countries (
            name, slug, code, capital, language, currency, currency_code,
            avg_tuition_annual_usd, avg_living_monthly_usd, overview,
            visa_requirements, work_permit_info, popular_cities
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, countries)
        conn.commit()

    # Get country IDs
    cursor.execute("SELECT id, slug FROM countries")
    c_map = {row["slug"]: row["id"] for row in cursor.fetchall()}

    # Check universities
    cursor.execute("SELECT COUNT(*) FROM universities")
    if cursor.fetchone()[0] == 0:
        universities = [
            (
                c_map["germany"], "Technical University of Munich (TUM)", "tum-germany", "Munich", 37,
                "https://www.tum.de",
                "Technical University of Munich is one of Europe's top universities, committed to excellence in research and teaching, interdisciplinary education, and the active promotion of young scientists.",
                "Bachelor's, Master's, PhD",
                "Informatics, Data Engineering, Mechanical Engineering, Robotics, Management & Technology",
                1500.0,
                "Recognized secondary school diploma / Bachelor's in relevant discipline, German or English language proficiency (IELTS 6.5+ or Goethe-Zertifikat C1 depending on track), Aptitude assessment interview/test.",
                "October (Winter), April (Summer)",
                "tum.jpg"
            ),
            (
                c_map["germany"], "RWTH Aachen University", "rwth-aachen", "Aachen", 106,
                "https://www.rwth-aachen.de",
                "RWTH Aachen University is a leading technical university in Germany, renowned for pioneering engineering disciplines and strong partnerships with multinational manufacturing enterprises.",
                "Bachelor's, Master's, PhD",
                "Automotive Engineering, Electrical Engineering, Computer Science, Metallurgy, Business Administration",
                1000.0,
                "Abitur-equivalent academic record, GRE recommended for international engineering applicants, proof of language skills (English B2/C1 or German TestDaF 4).",
                "October (Winter)",
                "rwth.jpg"
            ),
            (
                c_map["canada"], "University of Toronto", "university-of-toronto", "Toronto", 21,
                "https://www.utoronto.ca",
                "The University of Toronto is Canada's leading institution of learning and discovery, ranked amongst the world's most prestigious universities for medical, computing, and social research.",
                "Bachelor's, Master's, PhD",
                "Computer Science, Artificial Intelligence, Rotman MBA, Biomedical Engineering, Economics",
                32000.0,
                "High School GPA 3.7+ / Minimum undergraduate GPA 3.3/4.0 for Master's, IELTS 7.0 (no band below 6.5) or TOEFL iBT 100, Statement of Intent, 2-3 Letters of Reference.",
                "September (Fall), January (Winter)",
                "utoronto.jpg"
            ),
            (
                c_map["canada"], "University of British Columbia (UBC)", "ubc-canada", "Vancouver", 34,
                "https://www.ubc.ca",
                "Located on the stunning Pacific coast, UBC is a global center for research and teaching, consistently ranked among the top 20 public universities in the world.",
                "Bachelor's, Master's, PhD",
                "Environmental Sciences, Forestry, Software Systems, Sauder School of Business, Neuroscience",
                29000.0,
                "Strong academic standing in senior secondary or undergraduate degree, IELTS 6.5+ (minimum 6.0 in each component), personal profile essays, academic references.",
                "September (Winter Term 1), January (Winter Term 2)",
                "ubc.jpg"
            ),
            (
                c_map["australia"], "The University of Melbourne", "university-of-melbourne", "Melbourne", 14,
                "https://www.unimelb.edu.au",
                "Australia's number one university, renowned for pioneering research, distinctive Melbourne Curriculum, and rich cultural campus life in the heart of Melbourne.",
                "Bachelor's, Master's, PhD",
                "Data Science, Medicine, Law (Melbourne JD), Architecture, Commerce & Finance",
                31000.0,
                "Equivalent to Australian Year 12 with high ATAR / Bachelor degree with minimum 65-70% weighted average, IELTS 6.5+ (no band below 6.0), prerequisite subject requirements.",
                "February (Semester 1), July (Semester 2)",
                "unimelb.jpg"
            ),
            (
                c_map["australia"], "The University of Sydney", "university-of-sydney", "Sydney", 19,
                "https://www.sydney.edu.au",
                "One of Australia's first universities, combining neo-gothic quadrangle heritage with state-of-the-art nanoscience and business research laboratories.",
                "Bachelor's, Master's, PhD",
                "Aerospace Engineering, Media & Communications, Veterinary Science, International Business, Pharmacy",
                30000.0,
                "High academic attainment in relevant qualifications, IELTS Academic overall 6.5-7.0 depending on faculty, certified academic transcripts and syllabus if seeking credits.",
                "March (Semester 1), August (Semester 2)",
                "usyd.jpg"
            ),
            (
                c_map["united-kingdom"], "University of Oxford", "university-of-oxford", "Oxford", 3,
                "https://www.ox.ac.uk",
                "The oldest university in the English-speaking world, Oxford offers collegiate life, tutorial teaching methods, and unparalleled global academic prestige.",
                "Bachelor's, Master's, PhD",
                "Philosophy Politics and Economics (PPE), Computer Science, Law (BCL), Biochemistry, History",
                38000.0,
                "A*A*A to AAA at A-levels or equivalent international qualification (GPA 3.8+ for postgrad), admissions tests (e.g. MAT, TSA, LNAT), written work submission, academic interview.",
                "October (Michaelmas Term)",
                "oxford.jpg"
            ),
            (
                c_map["united-kingdom"], "Imperial College London", "imperial-college-london", "London", 6,
                "https://www.imperial.ac.uk",
                "Imperial College London is a world-renowned STEMB powerhouse focused exclusively on science, engineering, medicine, and business, situated in South Kensington.",
                "Bachelor's, Master's, PhD",
                "Computing & Software Engineering, Mechanical Engineering, Health Data Analytics, Climate Finance, Physics",
                36000.0,
                "High grade requirements (A*A*A at A-level or first-class degree equivalent), mathematics/physics prerequisites, IELTS 7.0 (minimum 6.5 in all elements).",
                "October (Autumn)",
                "imperial.jpg"
            ),
            (
                c_map["united-states"], "Massachusetts Institute of Technology (MIT)", "mit-usa", "Cambridge, MA", 1,
                "https://www.mit.edu",
                "MIT is a world leader in science, engineering, and technology innovation, celebrated for hands-on 'mens et manus' (mind and hand) education and entrepreneurial impact.",
                "Bachelor's, Master's, PhD",
                "Electrical Engineering & Computer Science (EECS), Artificial Intelligence, Physics, Sloan MBA, Aerospace",
                42000.0,
                "Holistic evaluation: extraordinary achievement in STEM subjects, SAT/ACT scores (undergraduate) or GRE scores (some graduate programs), IELTS 7.5+ or TOEFL 100+, 3 recommendation letters.",
                "September (Fall Term)",
                "mit.jpg"
            ),
            (
                c_map["united-states"], "Harvard University", "harvard-university", "Cambridge, MA", 4,
                "https://www.harvard.edu",
                "Harvard is the oldest higher education institution in the United States and a founding member of the Ivy League, boasting influential global alumni and vast libraries.",
                "Bachelor's, Master's, PhD",
                "Economics, Government, Harvard Business School MBA, Computer Science, Harvard Law JD",
                44000.0,
                "Highly selective admission: exceptional GPA and academic rigor, strong extracurricular leadership, essays, recommendations, TOEFL iBT 105+ or IELTS 7.5+.",
                "September (Fall Term)",
                "harvard.jpg"
            )
        ]
        cursor.executemany("""
        INSERT INTO universities (
            country_id, name, slug, city, world_ranking, website_url,
            description, degrees_offered, popular_courses, avg_tuition_usd,
            admission_requirements, intake_months, campus_image
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, universities)
        conn.commit()

    # Get university IDs
    cursor.execute("SELECT id, slug FROM universities")
    u_map = {row["slug"]: row["id"] for row in cursor.fetchall()}

    # Check scholarships
    cursor.execute("SELECT COUNT(*) FROM scholarships")
    if cursor.fetchone()[0] == 0:
        scholarships = [
            (
                u_map.get("tum-germany"), c_map["germany"],
                "DAAD Master Studies Scholarship",
                "German Academic Exchange Service (DAAD)",
                12000.0, "Monthly Stipend + Travel",
                "Graduates with excellent academic records holding a Bachelor's degree not older than 6 years. Open to all disciplines with priority for sustainable development fields.",
                "October 31 (Annual)",
                "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
                "Provides monthly allowance of €934, travel allowance, health insurance, and one-off study subsidy for international students pursuing a complete Master's degree in Germany."
            ),
            (
                u_map.get("rwth-aachen"), c_map["germany"],
                "Heinrich Böll Foundation Scholarships",
                "Heinrich Böll Foundation",
                11500.0, "Full Living Stipend",
                "International students who gained their university entrance qualification outside Germany, demonstrating outstanding academic records and social/political engagement.",
                "September 1 (Annual)",
                "https://www.boell.de/en/scholarships",
                "Covers full monthly maintenance stipend and health insurance for undergraduate and graduate students pursuing degrees in Germany."
            ),
            (
                u_map.get("university-of-toronto"), c_map["canada"],
                "Lester B. Pearson International Scholarship",
                "University of Toronto",
                38000.0, "Full Tuition + Residence",
                "Exceptional international high school students recognized for outstanding academic achievement, creative thinking, and community leadership.",
                "November 30 (Annual)",
                "https://future.utoronto.ca/pearson/",
                "The premier scholarship covers tuition, books, incidental fees, and full residence support for four years of undergraduate study at U of T."
            ),
            (
                u_map.get("ubc-canada"), c_map["canada"],
                "International Major Entrance Scholarship (IMES)",
                "University of British Columbia",
                20000.0, "Partial Tuition",
                "Exceptional international students entering undergraduate programs at UBC who exhibit academic excellence and extracurricular engagement.",
                "January 15 (Annual)",
                "https://you.ubc.ca/financial-planning/scholarships-awards-international-students/",
                "Awarded to incoming international undergraduate students, renewable for up to three additional years of study."
            ),
            (
                u_map.get("university-of-melbourne"), c_map["australia"],
                "Melbourne International Undergraduate Scholarship",
                "University of Melbourne",
                15000.0, "Tuition Fee Remission",
                "High-achieving international students who have received an unconditional offer for an undergraduate degree with top secondary school results.",
                "December 31 (Semester 1) / May 31 (Semester 2)",
                "https://scholarships.unimelb.edu.au/",
                "Provides either AUD $10,000 fee remission in the first year, 50% fee remission, or 100% fee remission for the duration of the undergraduate course."
            ),
            (
                u_map.get("usyd-canada", u_map.get("usyd-australia", u_map.get("the-university-of-sydney", list(u_map.values())[5]))), c_map["australia"],
                "Australia Awards Scholarship",
                "Department of Foreign Affairs and Trade (DFAT)",
                35000.0, "Full Scholarship",
                "Citizens of participating Indo-Pacific, African, and Middle-Eastern countries with minimum 2 years of work experience and leadership potential.",
                "April 30 (Annual)",
                "https://www.dfat.gov.au/people-to-people/australia-awards",
                "Covers full tuition fees, return air travel, establishment allowance, contribution to living expenses (CLE), and Overseas Student Health Cover (OSHC)."
            ),
            (
                u_map.get("oxford.jpg", u_map.get("university-of-oxford")), c_map["united-kingdom"],
                "Clarendon Fund Scholarship",
                "University of Oxford",
                45000.0, "Full Tuition + Living Grant",
                "All graduate applicants to Oxford with outstanding academic merit and research potential; automatically considered upon course application.",
                "January 10 (Course deadline)",
                "https://www.ox.ac.uk/clarendon",
                "Oxford's largest scholarship scheme, covering full course fees and a generous annual living stipend for Master's or DPhil students."
            ),
            (
                u_map.get("mit-usa"), c_map["united-states"],
                "Fulbright Foreign Student Program",
                "US Department of State",
                40000.0, "Full Tuition + Stipend",
                "Graduates and young professionals from over 160 partner nations with strong leadership track records and clear academic objectives.",
                "Varies by home country (March - October)",
                "https://foreign.fulbrightonline.org/",
                "Operates globally to fund graduate study in the United States, providing comprehensive tuition, living expenses, health insurance, and airfare."
            )
        ]
        cursor.executemany("""
        INSERT INTO scholarships (
            university_id, country_id, title, provider, award_amount_usd,
            coverage_type, eligibility_criteria, deadline, application_url, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, scholarships)
        conn.commit()

    # Seed Sample Student Account
    cursor.execute("SELECT id FROM users WHERE username = 'student'")
    student_user = cursor.fetchone()
    if not student_user:
        student_pw_hash = generate_password_hash("StudentPass123!")
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, role)
        VALUES ('student', 'student@example.com', ?, 'Alex Morgan (Demo Student)', 'student')
        """, (student_pw_hash,))
        student_id = cursor.lastrowid
        conn.commit()

        # Seed sample saved university for this student
        tum_id = u_map.get("tum-germany")
        utoronto_id = u_map.get("university-of-toronto")
        if tum_id:
            cursor.execute("INSERT OR IGNORE INTO saved_universities (user_id, university_id) VALUES (?, ?)", (student_id, tum_id))
        if utoronto_id:
            cursor.execute("INSERT OR IGNORE INTO saved_universities (user_id, university_id) VALUES (?, ?)", (student_id, utoronto_id))

        # Seed sample applications for this student
        if tum_id:
            cursor.execute("""
            INSERT INTO applications (
                user_id, university_id, degree_level, program_name, intake_year, intake_semester, status, notes
            ) VALUES (?, ?, 'Master', 'M.Sc. Informatics', 2026, 'Winter (October)', 'Under Review', 'Submitted transcripts and English score. Waiting for faculty aptitude interview call.')
            """, (student_id, tum_id))
        if utoronto_id:
            cursor.execute("""
            INSERT INTO applications (
                user_id, university_id, degree_level, program_name, intake_year, intake_semester, status, notes
            ) VALUES (?, ?, 'Master', 'Master of Science in Applied Computing (MScAC)', 2026, 'Fall (September)', 'Draft', 'Drafting personal statement and requesting letters of recommendation from professors.')
            """, (student_id, utoronto_id))
        conn.commit()

    # Seed or configure Admin Account safely
    cursor.execute("SELECT id FROM users WHERE role = 'admin'")
    admin_user = cursor.fetchone()
    if not admin_user:
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@globaledu.local')
        env_password = os.environ.get('ADMIN_PASSWORD')

        if env_password and env_password.strip():
            admin_password = env_password.strip()
            generated = False
        else:
            # Generate a secure random password on first run
            admin_password = secrets.token_urlsafe(12)
            generated = True

        admin_hash = generate_password_hash(admin_password)
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, role)
        VALUES (?, ?, ?, 'System Administrator', 'admin')
        """, (admin_username, admin_email, admin_hash))
        conn.commit()

        # Write credentials notice to database directory for local developer convenience
        creds_file = os.path.join(os.path.dirname(get_db_path()), '.admin_credentials.txt')
        with open(creds_file, 'w', encoding='utf-8') as f:
            f.write("GLOBAL EDU - Initial Local Development Admin Credentials\n")
            f.write("========================================================\n")
            f.write(f"Username: {admin_username}\n")
            f.write(f"Email:    {admin_email}\n")
            f.write(f"Password: {admin_password}\n")
            if generated:
                f.write("\nNote: This secure password was automatically generated because ADMIN_PASSWORD was not set in .env.\n")
                f.write("Keep this file safe and never commit it to source control.\n")

        print("*" * 65)
        print("  [SECURITY NOTICE] Admin account created for local development:")
        print(f"  Username: {admin_username}")
        print(f"  Password: {admin_password}")
        print(f"  Saved in: {creds_file}")
        print("*" * 65)
    elif os.environ.get('ADMIN_PASSWORD') and os.environ.get('ADMIN_PASSWORD').strip():
        # Update existing admin password if explicitly configured in environment / .env
        env_pw = os.environ.get('ADMIN_PASSWORD').strip()
        new_hash = generate_password_hash(env_pw)
        cursor.execute("UPDATE users SET password_hash = ? WHERE role = 'admin'", (new_hash,))
        conn.commit()
        creds_file = os.path.join(os.path.dirname(get_db_path()), '.admin_credentials.txt')
        with open(creds_file, 'w', encoding='utf-8') as f:
            f.write("GLOBAL EDU - Initial Local Development Admin Credentials\n")
            f.write("========================================================\n")
            f.write(f"Username: {os.environ.get('ADMIN_USERNAME', 'admin')}\n")
            f.write(f"Password: {env_pw}\n")

    # Seed sample contact messages
    cursor.execute("SELECT COUNT(*) FROM contact_messages")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO contact_messages (name, email, subject, message, is_read)
        VALUES (
            'Sophia Chen',
            'sophia.c@example.com',
            'Query about German Blocked Account requirements',
            'Hello Global Edu team, I am preparing my winter application for TUM and had a question regarding the acceptable providers for the blocked account in Germany. Could you clarify?',
            0
        )
        """)
        conn.commit()


# ==============================================================================
# Helper Query Functions for Application Logic
# ==============================================================================

def get_platform_stats():
    """Retrieve key platform counts for dashboards."""
    conn = get_db()
    cursor = conn.cursor()
    stats = {}
    stats['countries'] = cursor.execute("SELECT COUNT(*) FROM countries").fetchone()[0]
    stats['universities'] = cursor.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
    stats['scholarships'] = cursor.execute("SELECT COUNT(*) FROM scholarships").fetchone()[0]
    stats['students'] = cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    stats['applications'] = cursor.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    stats['unread_messages'] = cursor.execute("SELECT COUNT(*) FROM contact_messages WHERE is_read = 0").fetchone()[0]
    conn.close()
    return stats


def get_user_by_id(user_id):
    """Retrieve a user record by ID."""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def get_user_by_username_or_email(identifier):
    """Retrieve a user by username or email."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (identifier, identifier)
    ).fetchone()
    conn.close()
    return user


def create_user(username, email, password, full_name, role='student'):
    """Create a new user with securely hashed password."""
    conn = get_db()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, role)
        VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, full_name, role))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id, None
    except sqlite3.IntegrityError as e:
        return None, str(e)
    finally:
        conn.close()


def get_all_countries(search=None):
    """Retrieve all countries, optionally filtered by keyword."""
    conn = get_db()
    if search:
        query = """
        SELECT c.*, COUNT(u.id) as university_count
        FROM countries c
        LEFT JOIN universities u ON u.country_id = c.id
        WHERE c.name LIKE ? OR c.language LIKE ? OR c.popular_cities LIKE ?
        GROUP BY c.id
        ORDER BY c.name ASC
        """
        term = f"%{search}%"
        countries = conn.execute(query, (term, term, term)).fetchall()
    else:
        query = """
        SELECT c.*, COUNT(u.id) as university_count
        FROM countries c
        LEFT JOIN universities u ON u.country_id = c.id
        GROUP BY c.id
        ORDER BY c.name ASC
        """
        countries = conn.execute(query).fetchall()
    conn.close()
    return countries


def get_country_by_id(country_id):
    """Retrieve single country by ID."""
    conn = get_db()
    country = conn.execute("SELECT * FROM countries WHERE id = ?", (country_id,)).fetchone()
    conn.close()
    return country


def get_country_by_slug(slug):
    """Retrieve single country by slug."""
    conn = get_db()
    country = conn.execute("SELECT * FROM countries WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return country


def get_universities_by_country(country_id):
    """Retrieve all universities in a specific country."""
    conn = get_db()
    universities = conn.execute("""
    SELECT * FROM universities WHERE country_id = ? ORDER BY world_ranking ASC, name ASC
    """, (country_id,)).fetchall()
    conn.close()
    return universities


def get_scholarships_by_country(country_id):
    """Retrieve all scholarships available for a specific country."""
    conn = get_db()
    scholarships = conn.execute("""
    SELECT s.*, u.name as university_name
    FROM scholarships s
    LEFT JOIN universities u ON s.university_id = u.id
    WHERE s.country_id = ?
    ORDER BY s.award_amount_usd DESC
    """, (country_id,)).fetchall()
    conn.close()
    return scholarships


def filter_universities(country_id=None, degree=None, course=None, search=None, max_tuition=None):
    """Filter universities by country, degree level, course keyword, search keyword, and tuition limit."""
    conn = get_db()
    conditions = []
    params = []

    if country_id:
        conditions.append("u.country_id = ?")
        params.append(country_id)

    if degree:
        conditions.append("u.degrees_offered LIKE ?")
        params.append(f"%{degree}%")

    if course:
        conditions.append("u.popular_courses LIKE ?")
        params.append(f"%{course}%")

    if search:
        conditions.append("(u.name LIKE ? OR u.city LIKE ? OR u.description LIKE ? OR c.name LIKE ?)")
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if max_tuition:
        conditions.append("u.avg_tuition_usd <= ?")
        params.append(float(max_tuition))

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
    SELECT u.*, c.name as country_name, c.code as country_code, c.currency_code
    FROM universities u
    JOIN countries c ON u.country_id = c.id
    {where_clause}
    ORDER BY u.world_ranking ASC, u.name ASC
    """
    universities = conn.execute(query, params).fetchall()
    conn.close()
    return universities


def get_university_by_id(univ_id):
    """Retrieve single university with country data by ID."""
    conn = get_db()
    university = conn.execute("""
    SELECT u.*, c.name as country_name, c.code as country_code, c.currency as country_currency,
           c.currency_code, c.avg_living_monthly_usd as country_avg_living_usd
    FROM universities u
    JOIN countries c ON u.country_id = c.id
    WHERE u.id = ?
    """, (univ_id,)).fetchone()
    conn.close()
    return university


def filter_scholarships(country_id=None, coverage_type=None, search=None):
    """Filter scholarships by country, coverage type, and keyword."""
    conn = get_db()
    conditions = []
    params = []

    if country_id:
        conditions.append("s.country_id = ?")
        params.append(country_id)

    if coverage_type:
        conditions.append("s.coverage_type LIKE ?")
        params.append(f"%{coverage_type}%")

    if search:
        conditions.append("(s.title LIKE ? OR s.provider LIKE ? OR s.description LIKE ? OR s.eligibility_criteria LIKE ?)")
        term = f"%{search}%"
        params.extend([term, term, term, term])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
    SELECT s.*, c.name as country_name, c.code as country_code, u.name as university_name
    FROM scholarships s
    LEFT JOIN countries c ON s.country_id = c.id
    LEFT JOIN universities u ON s.university_id = u.id
    {where_clause}
    ORDER BY s.award_amount_usd DESC, s.title ASC
    """
    scholarships = conn.execute(query, params).fetchall()
    conn.close()
    return scholarships


def get_scholarship_by_id(scholarship_id):
    """Retrieve single scholarship with related country and university data."""
    conn = get_db()
    scholarship = conn.execute("""
    SELECT s.*, c.name as country_name, c.code as country_code, u.name as university_name
    FROM scholarships s
    LEFT JOIN countries c ON s.country_id = c.id
    LEFT JOIN universities u ON s.university_id = u.id
    WHERE s.id = ?
    """, (scholarship_id,)).fetchone()
    conn.close()
    return scholarship


# ---------------- Saved Universities Management ----------------

def is_university_saved(user_id, university_id):
    """Check if a university is already saved by a user."""
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM saved_universities WHERE user_id = ? AND university_id = ?",
        (user_id, university_id)
    ).fetchone()
    conn.close()
    return row is not None


def toggle_save_university(user_id, university_id):
    """Add or remove university from student's saved list."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM saved_universities WHERE user_id = ? AND university_id = ?",
        (user_id, university_id)
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute("DELETE FROM saved_universities WHERE id = ?", (existing["id"],))
        conn.commit()
        conn.close()
        return False, "University removed from your saved list."
    else:
        cursor.execute(
            "INSERT INTO saved_universities (user_id, university_id) VALUES (?, ?)",
            (user_id, university_id)
        )
        conn.commit()
        conn.close()
        return True, "University saved to your favorites!"


def get_saved_universities_for_user(user_id):
    """Retrieve all universities saved by a specific user."""
    conn = get_db()
    saved = conn.execute("""
    SELECT su.id as save_id, su.created_at as saved_at, u.*, c.name as country_name, c.code as country_code
    FROM saved_universities su
    JOIN universities u ON su.university_id = u.id
    JOIN countries c ON u.country_id = c.id
    WHERE su.user_id = ?
    ORDER BY su.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return saved


# ---------------- Application Planner Management ----------------

def get_applications_for_user(user_id):
    """Retrieve all applications created by a specific user with university and country details."""
    conn = get_db()
    apps = conn.execute("""
    SELECT a.*, u.name as university_name, u.city as university_city,
           c.name as country_name, c.code as country_code
    FROM applications a
    JOIN universities u ON a.university_id = u.id
    JOIN countries c ON u.country_id = c.id
    WHERE a.user_id = ?
    ORDER BY a.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return apps


def get_application_by_id_and_user(app_id, user_id):
    """Retrieve application strictly verifying user ownership."""
    conn = get_db()
    app_record = conn.execute("""
    SELECT a.*, u.name as university_name
    FROM applications a
    JOIN universities u ON a.university_id = u.id
    WHERE a.id = ? AND a.user_id = ?
    """, (app_id, user_id)).fetchone()
    conn.close()
    return app_record


def create_application(user_id, university_id, degree_level, program_name, intake_year, intake_semester, status='Draft', notes=None):
    """Create a new application record for a student."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO applications (
        user_id, university_id, degree_level, program_name, intake_year, intake_semester, status, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, university_id, degree_level, program_name, intake_year, intake_semester, status, notes))
    conn.commit()
    app_id = cursor.lastrowid
    conn.close()
    return app_id


def update_application(app_id, user_id, degree_level, program_name, intake_year, intake_semester, status, notes):
    """Update an application record strictly ensuring the user owns it."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE applications
    SET degree_level = ?, program_name = ?, intake_year = ?, intake_semester = ?,
        status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ? AND user_id = ?
    """, (degree_level, program_name, intake_year, intake_semester, status, notes, app_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def delete_application(app_id, user_id):
    """Delete an application record strictly verifying user ownership."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE id = ? AND user_id = ?", (app_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


# ---------------- Contact Form Submissions ----------------

def save_contact_message(name, email, subject, message):
    """Store contact form inquiry into SQLite."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO contact_messages (name, email, subject, message)
    VALUES (?, ?, ?, ?)
    """, (name, email, subject, message))
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id


def get_all_contact_messages():
    """Retrieve all contact form inquiries for the admin dashboard."""
    conn = get_db()
    messages = conn.execute("""
    SELECT * FROM contact_messages ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return messages


def mark_contact_message_read(msg_id):
    """Toggle or mark contact message as read."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE contact_messages SET is_read = 1 WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


def delete_contact_message(msg_id):
    """Delete a contact message."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contact_messages WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


# ---------------- Admin CRUD Helpers ----------------

def admin_create_country(name, slug, code, capital, language, currency, currency_code,
                         avg_tuition_annual_usd, avg_living_monthly_usd, overview,
                         visa_requirements, work_permit_info, popular_cities):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO countries (
        name, slug, code, capital, language, currency, currency_code,
        avg_tuition_annual_usd, avg_living_monthly_usd, overview,
        visa_requirements, work_permit_info, popular_cities
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, slug, code, capital, language, currency, currency_code,
          avg_tuition_annual_usd, avg_living_monthly_usd, overview,
          visa_requirements, work_permit_info, popular_cities))
    conn.commit()
    country_id = cursor.lastrowid
    conn.close()
    return country_id


def admin_update_country(country_id, name, slug, code, capital, language, currency, currency_code,
                         avg_tuition_annual_usd, avg_living_monthly_usd, overview,
                         visa_requirements, work_permit_info, popular_cities):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE countries SET
        name = ?, slug = ?, code = ?, capital = ?, language = ?, currency = ?, currency_code = ?,
        avg_tuition_annual_usd = ?, avg_living_monthly_usd = ?, overview = ?,
        visa_requirements = ?, work_permit_info = ?, popular_cities = ?
    WHERE id = ?
    """, (name, slug, code, capital, language, currency, currency_code,
          avg_tuition_annual_usd, avg_living_monthly_usd, overview,
          visa_requirements, work_permit_info, popular_cities, country_id))
    conn.commit()
    conn.close()


def admin_delete_country(country_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM countries WHERE id = ?", (country_id,))
    conn.commit()
    conn.close()


def admin_create_university(country_id, name, slug, city, world_ranking, website_url,
                           description, degrees_offered, popular_courses, avg_tuition_usd,
                           admission_requirements, intake_months, campus_image="default.jpg"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO universities (
        country_id, name, slug, city, world_ranking, website_url,
        description, degrees_offered, popular_courses, avg_tuition_usd,
        admission_requirements, intake_months, campus_image
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (country_id, name, slug, city, world_ranking, website_url,
          description, degrees_offered, popular_courses, avg_tuition_usd,
          admission_requirements, intake_months, campus_image))
    conn.commit()
    univ_id = cursor.lastrowid
    conn.close()
    return univ_id


def admin_update_university(univ_id, country_id, name, slug, city, world_ranking, website_url,
                           description, degrees_offered, popular_courses, avg_tuition_usd,
                           admission_requirements, intake_months, campus_image):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE universities SET
        country_id = ?, name = ?, slug = ?, city = ?, world_ranking = ?, website_url = ?,
        description = ?, degrees_offered = ?, popular_courses = ?, avg_tuition_usd = ?,
        admission_requirements = ?, intake_months = ?, campus_image = ?
    WHERE id = ?
    """, (country_id, name, slug, city, world_ranking, website_url,
          description, degrees_offered, popular_courses, avg_tuition_usd,
          admission_requirements, intake_months, campus_image, univ_id))
    conn.commit()
    conn.close()


def admin_delete_university(univ_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM universities WHERE id = ?", (univ_id,))
    conn.commit()
    conn.close()


def admin_create_scholarship(university_id, country_id, title, provider, award_amount_usd,
                            coverage_type, eligibility_criteria, deadline, application_url, description):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO scholarships (
        university_id, country_id, title, provider, award_amount_usd,
        coverage_type, eligibility_criteria, deadline, application_url, description
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (university_id, country_id, title, provider, award_amount_usd,
          coverage_type, eligibility_criteria, deadline, application_url, description))
    conn.commit()
    s_id = cursor.lastrowid
    conn.close()
    return s_id


def admin_update_scholarship(s_id, university_id, country_id, title, provider, award_amount_usd,
                            coverage_type, eligibility_criteria, deadline, application_url, description):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE scholarships SET
        university_id = ?, country_id = ?, title = ?, provider = ?, award_amount_usd = ?,
        coverage_type = ?, eligibility_criteria = ?, deadline = ?, application_url = ?, description = ?
    WHERE id = ?
    """, (university_id, country_id, title, provider, award_amount_usd,
          coverage_type, eligibility_criteria, deadline, application_url, description, s_id))
    conn.commit()
    conn.close()


def admin_delete_scholarship(s_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scholarships WHERE id = ?", (s_id,))
    conn.commit()
    conn.close()


def get_admin_credentials_info():
    """Retrieve administrator username and password from .admin_credentials.txt if available."""
    creds_file = os.path.join(os.path.dirname(get_db_path()), '.admin_credentials.txt')
    if os.path.exists(creds_file):
        info = {}
        try:
            with open(creds_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('Username:'):
                        info['username'] = line.split('Username:')[1].strip()
                    elif line.startswith('Password:'):
                        info['password'] = line.split('Password:')[1].strip()
            if 'username' in info and 'password' in info:
                return info
        except Exception:
            pass
    return None


def set_admin_password(username='admin', password=None, email='admin@globaledu.local'):
    """Set or reset administrator credentials and synchronize .admin_credentials.txt."""
    if not password:
        password = secrets.token_urlsafe(12)
    conn = get_db()
    cursor = conn.cursor()
    pw_hash = generate_password_hash(password)
    cursor.execute("SELECT id FROM users WHERE role = 'admin'")
    admin_row = cursor.fetchone()
    if admin_row:
        cursor.execute("UPDATE users SET username = ?, password_hash = ? WHERE id = ?", (username, pw_hash, admin_row['id']))
    else:
        cursor.execute("INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?, ?, ?, 'System Administrator', 'admin')", (username, email, pw_hash))
    conn.commit()
    conn.close()

    creds_file = os.path.join(os.path.dirname(get_db_path()), '.admin_credentials.txt')
    with open(creds_file, 'w', encoding='utf-8') as f:
        f.write("GLOBAL EDU - Initial Local Development Admin Credentials\n")
        f.write("========================================================\n")
        f.write(f"Username: {username}\n")
        f.write(f"Email:    {email}\n")
        f.write(f"Password: {password}\n")
    return username, password

