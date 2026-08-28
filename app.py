from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)

DATABASE = "database.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row

    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)

    if db is not None:
        db.close()


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():
    with app.app_context():
        db = get_db()

        # USERS TABLE
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE,
                password TEXT
            )
        """)

        # COMPANIES TABLE
        db.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                location TEXT
            )
        """)

        # JOBS TABLE
        db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company_id INTEGER,
                location TEXT,
                salary TEXT,
                job_type TEXT,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)

        # APPLICATIONS TABLE
        db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                job_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        """)

        db.commit()


init_db()


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Job Portal API Running",
        "endpoints": [
            "/register",
            "/login",
            "/company",
            "/companies",
            "/add_job",
            "/jobs",
            "/apply",
            "/my_applications",
            "/job/<job_id>/applications"
        ]
    })


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    # HASH PASSWORD BEFORE SAVING
    hashed_password = generate_password_hash(password)

    db = get_db()

    try:
        db.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, hashed_password)
        )

        db.commit()

        return jsonify({
            "message": "User registered successfully"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Email already exists"
        }), 409


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    db = get_db()

    user = db.execute(
        """
        SELECT * FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    # CHECK PASSWORD AGAINST HASH
    if user and check_password_hash(
        user["password"],
        password
    ):
        return jsonify({
            "message": "Login successful",
            "user_id": user["id"]
        }), 200

    return jsonify({
        "error": "Invalid credentials"
    }), 401


# =========================================================
# ADD COMPANY
# =========================================================

@app.route("/company", methods=["POST"])
def add_company():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    name = data.get("name")
    location = data.get("location")

    if not name:
        return jsonify({
            "error": "Company name is required"
        }), 400

    db = get_db()

    db.execute(
        """
        INSERT INTO companies (name, location)
        VALUES (?, ?)
        """,
        (name, location)
    )

    db.commit()

    return jsonify({
        "message": "Company added"
    }), 201


# =========================================================
# GET COMPANIES
# =========================================================

@app.route("/companies", methods=["GET"])
def get_companies():
    db = get_db()

    companies = db.execute(
        "SELECT * FROM companies"
    ).fetchall()

    return jsonify([
        dict(company)
        for company in companies
    ]), 200


# =========================================================
# ADD JOB
# =========================================================

@app.route("/add_job", methods=["POST"])
def add_job():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    title = data.get("title")
    company_id = data.get("company_id")
    location = data.get("location")
    salary = data.get("salary")
    job_type = data.get("job_type")

    if not title or not company_id:
        return jsonify({
            "error": "Title and company_id are required"
        }), 400

    db = get_db()

    # CHECK COMPANY EXISTS
    company = db.execute(
        """
        SELECT id FROM companies
        WHERE id = ?
        """,
        (company_id,)
    ).fetchone()

    if not company:
        return jsonify({
            "error": "Company not found"
        }), 404

    db.execute(
        """
        INSERT INTO jobs (
            title,
            company_id,
            location,
            salary,
            job_type
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            title,
            company_id,
            location,
            salary,
            job_type
        )
    )

    db.commit()

    return jsonify({
        "message": "Job added!"
    }), 201


# =========================================================
# GET JOBS
# =========================================================

@app.route("/jobs", methods=["GET"])
def get_jobs():
    db = get_db()

    location = request.args.get("location")

    if location:
        jobs = db.execute(
            """
            SELECT
                jobs.*,
                companies.name AS company_name
            FROM jobs
            LEFT JOIN companies
                ON jobs.company_id = companies.id
            WHERE jobs.location = ?
            """,
            (location,)
        ).fetchall()

    else:
        jobs = db.execute(
            """
            SELECT
                jobs.*,
                companies.name AS company_name
            FROM jobs
            LEFT JOIN companies
                ON jobs.company_id = companies.id
            """
        ).fetchall()

    return jsonify([
        dict(job)
        for job in jobs
    ]), 200


# =========================================================
# DELETE JOB
# =========================================================

@app.route("/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    db = get_db()

    job = db.execute(
        """
        SELECT id FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    ).fetchone()

    if not job:
        return jsonify({
            "error": "Job not found"
        }), 404

    db.execute(
        """
        DELETE FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    )

    db.commit()

    return jsonify({
        "message": "Job deleted"
    }), 200


# =========================================================
# APPLY FOR JOB
# =========================================================

@app.route("/apply", methods=["POST"])
def apply_job():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    user_id = data.get("user_id")
    job_id = data.get("job_id")

    if not user_id or not job_id:
        return jsonify({
            "error": "user_id and job_id are required"
        }), 400

    db = get_db()

    # CHECK USER
    user = db.execute(
        """
        SELECT id FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    # CHECK JOB
    job = db.execute(
        """
        SELECT id FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    ).fetchone()

    if not job:
        return jsonify({
            "error": "Job not found"
        }), 404

    # CHECK DUPLICATE APPLICATION
    existing = db.execute(
        """
        SELECT id
        FROM applications
        WHERE user_id = ? AND job_id = ?
        """,
        (user_id, job_id)
    ).fetchone()

    if existing:
        return jsonify({
            "error": "You have already applied for this job"
        }), 409

    db.execute(
        """
        INSERT INTO applications (user_id, job_id)
        VALUES (?, ?)
        """,
        (user_id, job_id)
    )

    db.commit()

    return jsonify({
        "message": "Application submitted!"
    }), 201


# =========================================================
# MY APPLICATIONS
# =========================================================

@app.route("/my_applications", methods=["GET"])
def my_applications():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({
            "error": "user_id is required"
        }), 400

    db = get_db()

    applications = db.execute(
        """
        SELECT
            applications.id,
            jobs.title,
            companies.name AS company,
            jobs.location,
            jobs.salary,
            jobs.job_type
        FROM applications
        JOIN jobs
            ON applications.job_id = jobs.id
        JOIN companies
            ON jobs.company_id = companies.id
        WHERE applications.user_id = ?
        """,
        (user_id,)
    ).fetchall()

    return jsonify([
        dict(application)
        for application in applications
    ]), 200


# =========================================================
# VIEW APPLICATIONS FOR A JOB
# =========================================================

@app.route("/job/<int:job_id>/applications", methods=["GET"])
def job_applications(job_id):
    db = get_db()

    # CHECK JOB EXISTS
    job = db.execute(
        """
        SELECT id FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    ).fetchone()

    if not job:
        return jsonify({
            "error": "Job not found"
        }), 404

    applications = db.execute(
        """
        SELECT
            users.id,
            users.name,
            users.email
        FROM applications
        JOIN users
            ON applications.user_id = users.id
        WHERE applications.job_id = ?
        """,
        (job_id,)
    ).fetchall()

    return jsonify([
        dict(application)
        for application in applications
    ]), 200


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )