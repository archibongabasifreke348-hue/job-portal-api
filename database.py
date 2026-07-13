import sqlite3
from flask import g

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db(app):
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
        # 3. JOBS TABLE
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

# Helper functions for each table
def create_user(name, email, password):
    db = get_db()
    db.execute('INSERT INTO users (name, email, password) VALUES (?,?,?)', (name, email, password))
    db.commit()

def get_user_by_email_password(email, password):
    db = get_db()
    return db.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password)).fetchone()

def create_company(name, location):
    db = get_db()
    db.execute('INSERT INTO companies (name, location) VALUES (?,?)', (name, location))
    db.commit()

def get_all_companies():
    db = get_db()
    return db.execute("SELECT * FROM companies").fetchall()

def create_job(title, company_id, location, salary, job_type):
    db = get_db()
    db.execute('INSERT INTO jobs (title, company_id, location, salary, job_type) VALUES (?,?,?,?,?)', 
               (title, company_id, location, salary, job_type))
    db.commit()

def get_all_jobs(location=None):
    db = get_db()
    if location:
        return db.execute("SELECT * FROM jobs WHERE location=?", (location,)).fetchall()
    return db.execute("SELECT * FROM jobs").fetchall()

def delete_job(job_id):
    db = get_db()
    db.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    db.commit()

def create_application(user_id, job_id):
    db = get_db()
    db.execute('INSERT INTO applications (user_id, job_id) VALUES (?,?)', (user_id, job_id))
    db.commit()

def get_applications_by_user(user_id):
    db = get_db()
    return db.execute('''SELECT jobs.title, companies.name as company 
                         FROM applications 
                         JOIN jobs ON applications.job_id = jobs.id
                         JOIN companies ON jobs.company_id = companies.id
                         WHERE applications.user_id=?''', (user_id,)).fetchall()

def get_applications_by_job(job_id):
    db = get_db()
    return db.execute('''SELECT users.name, users.email 
                         FROM applications 
                         JOIN users ON applications.user_id = users.id
                         WHERE applications.job_id=?''', (job_id,)).fetchall()