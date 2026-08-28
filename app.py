from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_connection, init_db

app = Flask(__name__)

# Create database tables when the application starts
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
            "/jobs/<job_id>",
            "/apply",
            "/my_applications",
            "/job/<job_id>/applications"
        ]
    }), 200


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

    # Hash password before storing it
    hashed_password = generate_password_hash(password)

    db = get_connection()

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

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return jsonify({
                "error": "Email already exists"
            }), 409

        return jsonify({
            "error": "Could not register user"
        }), 500

    finally:
        db.close()


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

    db = get_connection()

    try:
        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

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

    finally:
        db.close()


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

    db = get_connection()

    try:
        cursor = db.execute(
            """
            INSERT INTO companies (name, location)
            VALUES (?, ?)
            """,
            (name, location)
        )

        db.commit()

        return jsonify({
            "message": "Company added",
            "company_id": cursor.lastrowid
        }), 201

    finally:
        db.close()


# =========================================================
# GET COMPANIES
# =========================================================

@app.route("/companies", methods=["GET"])
def get_companies():
    db = get_connection()

    try:
        companies = db.execute(
            """
            SELECT *
            FROM companies
            ORDER BY id DESC
            """
        ).fetchall()

        return jsonify([
            dict(company)
            for company in companies
        ]), 200

    finally:
        db.close()


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

    db = get_connection()

    try:
        company = db.execute(
            """
            SELECT id
            FROM companies
            WHERE id = ?
            """,
            (company_id,)
        ).fetchone()

        if not company:
            return jsonify({
                "error": "Company not found"
            }), 404

        cursor = db.execute(
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
            "message": "Job added!",
            "job_id": cursor.lastrowid
        }), 201

    finally:
        db.close()


# =========================================================
# GET JOBS
# =========================================================

@app.route("/jobs", methods=["GET"])
def get_jobs():
    location = request.args.get("location")

    db = get_connection()

    try:
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
                ORDER BY jobs.id DESC
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
                ORDER BY jobs.id DESC
                """
            ).fetchall()

        return jsonify([
            dict(job)
            for job in jobs
        ]), 200

    finally:
        db.close()


# =========================================================
# DELETE JOB
# =========================================================

@app.route("/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    db = get_connection()

    try:
        job = db.execute(
            """
            SELECT id
            FROM jobs
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
            DELETE FROM applications
            WHERE job_id = ?
            """,
            (job_id,)
        )

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

    finally:
        db.close()


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

    db = get_connection()

    try:
        user = db.execute(
            """
            SELECT id
           