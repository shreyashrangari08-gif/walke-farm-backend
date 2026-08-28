from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import jwt
import datetime
import os
from functools import wraps

# Setup app to serve index.html directly from root folder
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

SECRET_KEY = "WalkeFarm#Secure$Key_2026"

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# 1. FIX 404: DIRECT WEBSITE LOAD ON ROOT URL
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# 2. SERVE IMAGES
@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images', filename)

ADMIN_EMAILS = ["shreyashrangari08@gmail.com", "soniyasheikh594@gmail.com"]

# Admin Verification
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"status": "error", "message": "Token missing"}), 401
        try:
            token = token.replace("Bearer ", "")
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if data.get('role') != 'admin':
                return jsonify({"status": "error", "message": "Unauthorized Admin Access"}), 403
        except Exception:
            return jsonify({"status": "error", "message": "Session expired"}), 401
        return f(*args, **kwargs)
    return decorated

# Login API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE LOWER(TRIM(email)) = ?", (email,)).fetchone()
    conn.close()

    valid_password = False
    if user:
        if user['password'].startswith(('pbkdf2:', 'scrypt:', 'bcrypt:')):
            valid_password = check_password_hash(user['password'], password)
        else:
            valid_password = (user['password'] == password)

    if user and valid_password:
        role = "admin" if email in ADMIN_EMAILS else user['role']
        token = jwt.encode({
            "email": user['email'],
            "role": role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({
            "status": "success",
            "email": user['email'],
            "role": role,
            "token": token
        }), 200

    return jsonify({"status": "error", "message": "Invalid email or password"}), 401

# Signup API
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400

    hashed_pw = generate_password_hash(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password, role) VALUES (?, ?, 'user')", (email, hashed_pw))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Account created successfully!"}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"status": "error", "message": "Email already registered"}), 400

# Plots API
@app.route('/api/plots/<slug>', methods=['GET'])
def get_plots(slug):
    conn = get_db_connection()
    plots = conn.execute("SELECT * FROM plots WHERE project_slug = ?", (slug,)).fetchall()
    conn.close()
    return jsonify([dict(p) for p in plots]), 200

# Enquiry API
@app.route('/api/enquiry', methods=['POST'])
def submit_enquiry():
    data = request.json or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO enquiries (name, phone, project_name, plot_size, visit_date, message)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.get('name'), data.get('phone'), data.get('project_name'),
        data.get('plot_size'), data.get('visit_date'), data.get('message')
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Booking submitted successfully!"}), 201

# Admin APIs
@app.route('/api/admin/enquiries', methods=['GET'])
@admin_required
def get_admin_enquiries():
    conn = get_db_connection()
    enquiries = conn.execute('SELECT * FROM enquiries ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(e) for e in enquiries]), 200

@app.route('/api/admin/plots', methods=['GET'])
@admin_required
def get_admin_plots():
    conn = get_db_connection()
    plots = conn.execute('SELECT * FROM plots ORDER BY project_slug, id').fetchall()
    conn.close()
    return jsonify([dict(p) for p in plots]), 200

@app.route('/api/admin/update-plot-status', methods=['POST'])
@admin_required
def update_plot_status():
    data = request.json or {}
    plot_id = data.get('id')
    new_status = data.get('status')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE plots SET status = ? WHERE id = ?', (new_status, plot_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Plot status updated to {new_status}!"}), 200

@app.route('/api/admin/export-csv', methods=['GET'])
def export_csv():
    conn = get_db_connection()
    enquiries = conn.execute('SELECT * FROM enquiries ORDER BY created_at DESC').fetchall()
    conn.close()
    csv_data = "ID,Name,Phone,Project,Plot Size,Visit Date,Lead Status,Created At,Message\n"
    for e in enquiries:
        clean_msg = (e['message'] or '').replace(',', ' ')
        csv_data += f"{e['id']},\"{e['name']}\",=\"{e['phone']}\",\"{e['project_name']}\",\"{e['plot_size']}\",{e['visit_date']},{e['status']},{e['created_at']},\"{clean_msg}\"\n"
    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=Walke_Farm_Bookings.csv"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)