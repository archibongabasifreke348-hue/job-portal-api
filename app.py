from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        # 1. USERS TABLE
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            email TEXT UNIQUE, 
            password TEXT)''')
        # 2. COMPANIES TABLE
        db.execute('''CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            location TEXT)''')
        # 3. JOBS TABLE - now linked to company
        db.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT, 
            company_id INTEGER,
            location TEXT,
            salary TEXT,
            job_type TEXT,
            FOREIGN KEY (company_id) REFERENCES companies (id))''')
        # 4. APPLICATIONS TABLE
        db.execute('''CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER, 
            job_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (job_id) REFERENCES jobs (id))''')
        db.commit()

init_db()

@app.route("/")
def home():
    return jsonify({"message": "Job Portal API Running", "endpoints": ["/register", "/login", "/companies", "/jobs", "/apply"]})

### ===== 1. USER ENDPOINTS ===== ###
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    db = get_db()
    try:
        db.execute('INSERT INTO users (name, email, password) VALUES (?,?,?)', 
                   (data['name'], data['email'], data['password']))
        db.commit()
        return jsonify({"message": "User registered successfully"})
    except:
        return jsonify({"error": "Email already exists"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email=? AND password=?', 
                      (data['email'], data['password'])).fetchone()
    if user:
        return jsonify({"message": "Login successful", "user_id": user['id']})
    return jsonify({"error": "Invalid credentials"}), 401

### ===== 2. COMPANY ENDPOINTS ===== ###
@app.route("/company", methods=["POST"])
def add_company():
    data = request.get_json()
    db = get_db()
    db.execute('INSERT INTO companies (name, location) VALUES (?,?)', 
               (data['name'], data['location']))
    db.commit()
    return jsonify({"message": "Company added"})

@app.route("/companies", methods=["GET"])
def get_companies():
    db = get_db()
    companies = db.execute("SELECT * FROM companies").fetchall()
    return jsonify([dict(c) for c in companies])

### ===== 3. JOB ENDPOINTS ===== ###
@app.route("/add_job", methods=["POST"])
def add_job():
    data = request.get_json()
    db = get_db()
    db.execute('INSERT INTO jobs (title, company_id, location, salary, job_type) VALUES (?,?,?,?,?)', 
               (data['title'], data['company_id'], data.get('location'), data.get('salary'), data.get('job_type')))
    db.commit()
    return jsonify({"message": "Job added!"})

@app.route("/jobs", methods=["GET"])
def get_jobs():
    db = get_db()
    location = request.args.get('location')
    if location:
        jobs = db.execute("SELECT * FROM jobs WHERE location=?", (location,)).fetchall()
    else:
        jobs = db.execute("SELECT * FROM jobs").fetchall()
    return jsonify([dict(job) for job in jobs])

@app.route("/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    db = get_db()
    db.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    db.commit()
    return jsonify({"message": "Job deleted"})

### ===== 4. APPLICATION ENDPOINTS ===== ###
@app.route("/apply", methods=["POST"])
def apply_job():
    data = request.get_json()
    db = get_db()
    db.execute('INSERT INTO applications (user_id, job_id) VALUES (?,?)', 
               (data['user_id'], data['job_id']))
    db.commit()
    return jsonify({"message": "Application submitted!"})

@app.route("/my_applications", methods=["GET"])
def my_applications():
    user_id = request.args.get('user_id')
    db = get_db()
    apps = db.execute('''SELECT jobs.title, companies.name as company 
                         FROM applications 
                         JOIN jobs ON applications.job_id = jobs.id
                         JOIN companies ON jobs.company_id = companies.id
                         WHERE applications.user_id=?''', (user_id,)).fetchall()
    return jsonify([dict(a) for a in apps])

@app.route("/job/<int:job_id>/applications", methods=["GET"])
def job_applications(job_id):
    db = get_db()
    apps = db.execute('''SELECT users.name, users.email 
                         FROM applications 
                         JOIN users ON applications.user_id = users.id
                         WHERE applications.job_id=?''', (job_id,)).fetchall()
    return jsonify([dict(a) for a in apps])