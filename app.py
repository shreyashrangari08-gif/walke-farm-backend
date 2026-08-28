from flask import Flask, request, jsonify, Response, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import jwt
import datetime
import os
from functools import wraps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
CORS(app)

SECRET_KEY = "WalkeFarm#Secure$Key_2026"

def get_db_connection():
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'database.db'))
    conn.row_factory = sqlite3.Row
    return conn

def init_advanced_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check & update enquiries table for CRM stages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            project_name TEXT NOT NULL,
            plot_size TEXT NOT NULL,
            visit_date TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'New Lead',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check & update interactive plots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_slug TEXT NOT NULL,
            plot_no TEXT NOT NULL,
            size TEXT NOT NULL,
            rate TEXT NOT NULL,
            total_price TEXT NOT NULL,
            emi_plan TEXT NOT NULL,
            status TEXT DEFAULT 'Available'
        )
    ''')
    
    # Insert initial layout plots if empty
    cursor.execute('SELECT COUNT(*) as count FROM plots')
    if cursor.fetchone()['count'] == 0:
        sample_plots = [
            ('degma', 'P-01', '3,000 sq.ft.', '₹450/sq.ft.', '₹13.5 Lakh', '₹50,000/mo (24M 0%)', 'Available'),
            ('degma', 'P-02', '3,000 sq.ft.', '₹450/sq.ft.', '₹13.5 Lakh', '₹50,000/mo (24M 0%)', 'Booked'),
            ('degma', 'P-03', '6,000 sq.ft.', '₹450/sq.ft.', '₹27 Lakh', '₹1,00,000/mo (24M 0%)', 'Available'),
            ('degma', 'P-04', '6,000 sq.ft.', '₹450/sq.ft.', '₹27 Lakh', '₹1,00,000/mo (24M 0%)', 'On Hold'),
            ('degma', 'P-05', '11,000 sq.ft.', '₹450/sq.ft.', '₹49.5 Lakh', '₹1.83 Lakh/mo (24M 0%)', 'Available'),
            ('degma', 'P-06', '22,000 sq.ft.', '₹450/sq.ft.', '₹99 Lakh', '₹3.75 Lakh/mo (24M 0%)', 'Available'),
            ('strawberry', 'C-01', '1,114 sq.ft.', 'Furnished', '₹24 Lakh', '90% Bank Loan / 0% Co', 'Available'),
            ('strawberry', 'C-02', '1,114 sq.ft.', 'Furnished', '₹24 Lakh', '90% Bank Loan / 0% Co', 'Booked'),
            ('mindgame', 'M-01', '1,000 sq.ft.', '₹1,400/sq.ft.', '₹14 Lakh', '0% Interest EMI', 'Available'),
            ('mindgame', 'M-02', '2,000 sq.ft.', '₹1,400/sq.ft.', '₹28 Lakh', '0% Interest EMI', 'Available'),
            ('mindgame', 'M-03', '5,000 sq.ft.', '₹1,400/sq.ft.', '₹70 Lakh', '0% Commercial EMI', 'Available')
        ]
        cursor.executemany('''
            INSERT INTO plots (project_slug, plot_no, size, rate, total_price, emi_plan, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_plots)

    conn.commit()
    conn.close()

init_advanced_db()

@app.route('/')
def serve_index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/images/<path:filename>')
def serve_images(filename):
    clean_name = os.path.basename(filename)
    root_file = os.path.join(BASE_DIR, clean_name)
    images_dir_file = os.path.join(BASE_DIR, 'images', clean_name)
    if os.path.isfile(root_file):
        return send_file(root_file)
    elif os.path.isfile(images_dir_file):
        return send_file(images_dir_file)
    return "Image Not Found", 404

ADMIN_EMAILS = ["shreyashrangari08@gmail.com", "soniyasheikh594@gmail.com"]

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
        return jsonify({"status": "success", "email": user['email'], "role": role, "token": token}), 200

    return jsonify({"status": "error", "message": "Invalid email or password"}), 401

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

@app.route('/api/plots/<slug>', methods=['GET'])
def get_plots(slug):
    conn = get_db_connection()
    plots = conn.execute("SELECT * FROM plots WHERE project_slug = ?", (slug,)).fetchall()
    conn.close()
    return jsonify([dict(p) for p in plots]), 200

@app.route('/api/enquiry', methods=['POST'])
def submit_enquiry():
    data = request.json or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO enquiries (name, phone, project_name, plot_size, visit_date, message, status)
        VALUES (?, ?, ?, ?, ?, ?, 'New Lead')
    ''', (
        data.get('name'), data.get('phone'), data.get('project_name'),
        data.get('plot_size'), data.get('visit_date'), data.get('message')
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Lead captured successfully!"}), 201

# --- ADVANCED CRM APIs ---
@app.route('/api/admin/enquiries', methods=['GET'])
@admin_required
def get_admin_enquiries():
    conn = get_db_connection()
    enquiries = conn.execute('SELECT * FROM enquiries ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(e) for e in enquiries]), 200

@app.route('/api/admin/update-lead-status', methods=['POST'])
@admin_required
def update_lead_status():
    data = request.json or {}
    lead_id = data.get('id')
    new_status = data.get('status')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE enquiries SET status = ? WHERE id = ?', (new_status, lead_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Lead status moved to {new_status}!"}), 200

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
    csv_data = "ID,Name,Phone,Project,Plot Size,Visit Date,CRM Pipeline Stage,Created At,Message\n"
    for e in enquiries:
        clean_msg = (e['message'] or '').replace(',', ' ')
        csv_data += f"{e['id']},\"{e['name']}\",=\"{e['phone']}\",\"{e['project_name']}\",\"{e['plot_size']}\",{e['visit_date']},{e['status']},{e['created_at']},\"{clean_msg}\"\n"
    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=Walke_Farm_Bookings.csv"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)