from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_db, get_db_connection

app = Flask(__name__)
CORS(app) # This lets Frontend connect to you

# Run this once when server starts
init_db()

# 1. REGISTER
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, email, password) VALUES (?,?,?)',
                     (username, email, password))
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except:
        return jsonify({"error": "Username or Email already exists"}), 400
    finally:
        conn.close()

# 2. LOGIN
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username =? AND password =?', 
                        (username, password)).fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful", "user_id": user['id']}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# 3. GET ALL JOBS
@app.route('/jobs', methods=['GET'])
def get_jobs():
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs').fetchall()
    conn.close()
    return jsonify([dict(job) for job in jobs])

# 4. APPLY FOR JOB
@app.route('/apply', methods=['POST'])
def apply_job():
    data = request.get_json()
    user_id = data.get('user_id')
    job_id = data.get('job_id')

    conn = get_db_connection()
    conn.execute('INSERT INTO applications (user_id, job_id) VALUES (?,?)', (user_id, job_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Application submitted"}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)