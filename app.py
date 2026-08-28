import os
from functools import wraps

import jwt
from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_connection, init_db


app = Flask(__name__)

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "development-secret-key-change-this"
)

init_db()


# =========================================================
# JWT AUTHENTICATION
# =========================================================

def create_token(user_id):
    payload = {
        "user_id": user_id
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm="HS256"
    )


def token_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        authorization = request.headers.get("Authorization")

        if not authorization:
            return jsonify({
                "error": "Authorization token is required"
            }), 401

        parts = authorization.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "error": "Use Authorization: Bearer <token>"
            }), 401

        token = parts[1]

        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"]
            )

            user_id = payload.get("user_id")

            if not user_id:
                return jsonify({
                    "error": "Invalid token"
                }), 401

        except jwt.ExpiredSignatureError:
            return jsonify({
                "error": "Token has expired"
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                "error": "Invalid token"
            }), 401

        return function(user_id, *args, **kwargs)

    return decorated


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Job Portal API Running",
        "endpoints": [
            "POST /register",
            "POST /login",
            "POST /company",
            "GET /companies",
            "POST /add_job",
            "GET /jobs",
            "DELETE /jobs/<job_id>",
            "POST /apply",
            "GET /my_applications",
            "GET /job/<job_id>/applications"
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

    hashed_password = generate_password_hash(password)

    db = get_connection()

    try:
        cursor = db.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, hashed_password)
        )

        db.commit()

        return jsonify({
            "message": "User registered successfully",
            "user_id": cursor.lastrowid
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Email already exists"
        }), 409

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

        if not user or not check_password_hash(
            user["password"],
            password
        ):
            return jsonify({
                "error": "Invalid credentials"
            }), 401

        token = create_token(user["id"])

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user_id": user["id"]
        }), 200

    finally:
        db.close()


# =========================================================
# ADD COMPANY
# =========================================================

@app.route("/company", methods=["POST"])
@token_required
def add_company(current_user_id):
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
@token_required
def add_job(current_user_id):
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
@token_required
def delete_job(current_user_id, job_id):
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
@token_required
def apply_job(current_user_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    job_id = data.get("job_id")

    if not job_id:
        return jsonify({
            "error": "job_id is required"
        }), 400

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

        existing = db.execute(
            """
            SELECT id
            FROM applications
            WHERE user_id = ? AND job_id = ?
            """,
            (current_user_id, job_id)
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
            (current_user_id, job_id)
        )

        db.commit()

        return jsonify({
            "message": "Application submitted!"
        }), 201

    finally:
        db.close()


# =========================================================
# MY APPLICATIONS
# =========================================================

@app.route("/my_applications", methods=["GET"])
@token_required
def my_applications(current_user_id):
    db = get_connection()

    try:
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
            ORDER BY applications.id DESC
            """,
            (current_user_id,)
        ).fetchall()

        return jsonify([
            dict(application)
            for application in applications
        ]), 200

    finally:
        db.close()


# =========================================================
# VIEW APPLICATIONS FOR A JOB
# =========================================================

@app.route("/job/<int:job_id>/applications", methods=["GET"])
@token_required
def job_applications(current_user_id, job_id):
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
            ORDER BY applications.id DESC
            """,
            (job_id,)
        ).fetchall()

        return jsonify([
            dict(application)
            for application in applications
        ]), 200

    finally:
        db.close()


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )