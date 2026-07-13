import sqlite3
from contextlib import contextmanager

DATABASE = 'database.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            email TEXT UNIQUE, 
            password TEXT)''')
        db.execute('''CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            location TEXT)''')
        db.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT, 
            company_id INTEGER,
            location TEXT,
            salary TEXT,
            job_type TEXT,
            FOREIGN KEY (company_id) REFERENCES companies (id))''')
        db.execute('''CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER, 
            job_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (job_id) REFERENCES jobs (id))''')

# Helper functions - same as Flask version
def create_user(name, email, password):
    with get_db() as db:
        db.execute('INSERT INTO users (name, email, password) VALUES (?,?,?)', (name, email, password))

def get_user_by_email_password(email, password):
    with get_db() as db:
        return db.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password)).fetchone()

def create_company(name, location):
    with get_db() as db:
        db.execute('INSERT INTO companies (name, location) VALUES (?,?)', (name, location))

def get_all_companies():
    with get_db() as db:
        return db.execute("SELECT * FROM companies").fetchall()

def create_job(title, company_id, location, salary, job_type):
    with get_db() as db:
        db.execute('INSERT INTO jobs (title, company_id, location, salary, job_type) VALUES (?,?,?,?,?)', 
                   (title, company_id, location, salary, job_type))

def get_all_jobs(location=None):
    with get_db() as db:
        if location:
            return db.execute("SELECT * FROM jobs WHERE location=?", (location,)).fetchall()
        return db.execute("SELECT * FROM jobs").fetchall()

def delete_job(job_id):
    with get_db() as db:
        db.execute("DELETE FROM jobs WHERE id=?", (job_id,))

def create_application(user_id, job_id):
    with get_db() as db:
        db.execute('INSERT INTO applications (user_id, job_id) VALUES (?,?)', (user_id, job_id))

def get_applications_by_user(user_id