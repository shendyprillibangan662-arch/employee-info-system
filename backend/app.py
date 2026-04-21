from flask import Flask, request, session, jsonify
import sqlite3
from functools import wraps
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_in_production'
# Allow CORS for localhost frontend (e.g., if you run a simple server or just file://)
CORS(app, supports_credentials=True)

# --- DATABASE CONNECTION ---
def get_db_connection():
    import os
    db_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# --- AUTHENTICATION ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'username': session.get('username')})
    return jsonify({'authenticated': False}), 401

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Missing JSON body'}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

# --- ROUTES / PAGES ---
@app.route('/api/dashboard', methods=['GET'])
@login_required
def dashboard():
    conn = get_db_connection()
    
    active_count = conn.execute("SELECT COUNT(*) FROM employees WHERE status = 'Active'").fetchone()[0]
    permanent_count = conn.execute("SELECT COUNT(*) FROM employees WHERE status = 'Permanent'").fetchone()[0]
    temporary_count = conn.execute("SELECT COUNT(*) FROM employees WHERE status = 'Temporary'").fetchone()[0]
    separated_count = conn.execute("SELECT COUNT(*) FROM employees WHERE status = 'Separated'").fetchone()[0]
    
    try:
        activities_rows = conn.execute("SELECT * FROM activities ORDER BY id DESC LIMIT 10").fetchall()
        activities = [dict(ix) for ix in activities_rows]
    except:
        activities = []
    
    conn.close()
    
    return jsonify({
        'stats': {
            'active': active_count,
            'permanent': permanent_count,
            'temporary': temporary_count,
            'separated': separated_count
        },
        'activities': activities
    })

@app.route('/api/employees', methods=['GET'])
@login_required
def employees():
    search = request.args.get('search', '')
    conn = get_db_connection()
    
    if search:
        rows = conn.execute("SELECT * FROM employees WHERE first_name LIKE ? OR last_name LIKE ? ORDER BY last_name ASC, first_name ASC", ('%'+search+'%', '%'+search+'%')).fetchall()
    else:
        rows = conn.execute("SELECT * FROM employees ORDER BY last_name ASC, first_name ASC").fetchall()
        
    conn.close()
    
    employees_list = [dict(ix) for ix in rows]
    return jsonify({'employees': employees_list})

# --- ACTIONS ---
@app.route('/api/add', methods=['POST'])
@login_required
def add():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Missing data'}), 400
        
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    status = data.get('status')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO employees (first_name, last_name, status) VALUES (?, ?, ?)', (first_name, last_name, status))
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    employee_name = f"{first_name} {last_name}"
    conn.execute('INSERT INTO activities (activity, employee, date) VALUES (?, ?, ?)', ('Added Employee', employee_name, date_str))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/delete/<int:id>', methods=['DELETE'])
@login_required
def delete(id):
    conn = get_db_connection()
    
    # Get employee details to log activity
    employee = conn.execute("SELECT * FROM employees WHERE id = ?", (id,)).fetchone()
    if employee:
        employee_name = f"{employee['first_name']} {employee['last_name']}"
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute('INSERT INTO activities (activity, employee, date) VALUES (?, ?, ?)', ('Deleted Employee', employee_name, date_str))
        
        conn.execute("DELETE FROM employees WHERE id = ?", (id,))
        conn.commit()
    
    conn.close()
    return jsonify({'success': True})

# --- RUN APP ---
if __name__ == "__main__":
    app.run(debug=True, port=5000)