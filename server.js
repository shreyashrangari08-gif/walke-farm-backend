const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const jwt = require('jsonwebtoken');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;
const JWT_SECRET = process.env.JWT_SECRET || 'walke_farm_secret_jwt_key_2026';

app.use(cors());
app.use(express.json());

// Serve static frontend if hosted together
app.use(express.static(path.join(__dirname, 'public')));

// Database Initialization
const db = new sqlite3.Database('./walke_farm.db', (err) => {
  if (err) console.error('Database connection error:', err);
  else console.log('Connected to SQLite Database.');
});

// Create Required Tables
db.serialize(() => {
  // 1. Users Table
  db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'user'
  )`);

  // 2. Enquiries / Leads Table
  db.run(`CREATE TABLE IF NOT EXISTS enquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT,
    name TEXT,
    phone TEXT,
    plot_size TEXT,
    visit_date TEXT,
    message TEXT,
    status TEXT DEFAULT 'New Lead',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  // 3. Plots Management Table
  db.run(`CREATE TABLE IF NOT EXISTS plots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug TEXT,
    plot_no TEXT,
    size TEXT,
    total_price TEXT,
    status TEXT DEFAULT 'Available'
  )`);

  // 4. NEW: Priority Plot Hold Payments Table (₹4,999 Non-Refundable)
  db.run(`CREATE TABLE IF NOT EXISTS plot_holds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plot_no TEXT,
    project_name TEXT,
    name TEXT,
    phone TEXT,
    email TEXT,
    txn_id TEXT,
    amount INTEGER DEFAULT 4999,
    status TEXT DEFAULT 'PENDING_VERIFICATION',
    created_at TEXT
  )`);

  // Seed Default Admin if not exists
  db.get("SELECT COUNT(*) as count FROM users WHERE email = 'admin@walkefarm.com'", (err, row) => {
    if (row && row.count === 0) {
      db.run("INSERT INTO users (email, password, role) VALUES ('admin@walkefarm.com', 'admin123', 'admin')");
    }
  });

  // Seed Default Plots
  db.get("SELECT COUNT(*) as count FROM plots", (err, row) => {
    if (row && row.count === 0) {
      const defaultPlots = [
        ['degma', 'P-01', '3,000 sq.ft.', '₹13,00,000', 'Available'],
        ['degma', 'P-02', '3,000 sq.ft.', '₹13,00,000', 'Booked'],
        ['degma', 'P-03', '6,000 sq.ft.', '₹27,00,000', 'Available'],
        ['degma', 'P-04', '6,000 sq.ft.', '₹27,00,000', 'On Hold'],
        ['degma', 'P-05', '11,000 sq.ft.', '₹49,00,000', 'Available'],
        ['degma', 'P-06', '22,000 sq.ft.', '₹99,00,000', 'Available'],
        ['strawberry', 'C-01', 'Furnished Cottage', '₹24,00,000', 'Available'],
        ['strawberry', 'C-02', 'Furnished Cottage', '₹24,00,000', 'Booked'],
        ['strawberry', 'P-01', '1,000 sq.ft.', '₹14,00,000', 'Available'],
        ['mindgame', 'M-01', '1,000 sq.ft.', '₹14,00,000', 'Available'],
        ['mindgame', 'M-02', '2,000 sq.ft.', '₹28,00,000', 'Available'],
        ['mindgame', 'M-03', '5,000 sq.ft. Commercial', '₹70,00,000', 'Available']
      ];
      const stmt = db.prepare("INSERT INTO plots (project_slug, plot_no, size, total_price, status) VALUES (?, ?, ?, ?, ?)");
      defaultPlots.forEach(p => stmt.run(p));
      stmt.finalize();
    }
  });
});

// Middleware for Admin Auth
function authenticateAdmin(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader) return res.status(401).json({ message: 'Token missing' });
  const token = authHeader.split(' ')[1];
  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err || user.role !== 'admin') return res.status(403).json({ message: 'Forbidden: Admin Only' });
    req.user = user;
    next();
  });
}

// ---------------- ROUTES ----------------

// 1. Auth Routes
app.post('/api/signup', (req, res) => {
  const { email, password } = req.body;
  db.run("INSERT INTO users (email, password, role) VALUES (?, ?, 'user')", [email, password], function(err) {
    if (err) return res.status(400).json({ status: 'error', message: 'User already exists or database error.' });
    res.json({ status: 'success', message: 'User created successfully' });
  });
});

app.post('/api/login', (req, res) => {
  const { email, password } = req.body;
  db.get("SELECT * FROM users WHERE email = ? AND password = ?", [email, password], (err, user) => {
    if (err || !user) return res.status(401).json({ status: 'error', message: 'Invalid email or password' });
    const token = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: '7d' });
    res.json({ status: 'success', token, email: user.email, role: user.role });
  });
});

// 2. Enquiry Lead Route
app.post('/api/enquiry', (req, res) => {
  const { project_name, name, phone, plot_size, visit_date, message } = req.body;
  db.run(
    "INSERT INTO enquiries (project_name, name, phone, plot_size, visit_date, message) VALUES (?, ?, ?, ?, ?, ?)",
    [project_name, name, phone, plot_size, visit_date, message || ''],
    function(err) {
      if (err) return res.status(500).json({ status: 'error', message: err.message });
      res.json({ status: 'success', id: this.lastID });
    }
  );
});

// 3. Priority Plot Hold Registration Route (₹4,999)
app.post('/api/plot-hold', (req, res) => {
  const { plot_no, project_name, name, phone, email, txn_id } = req.body;
  const timestamp = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });

  db.run(
    `INSERT INTO plot_holds (plot_no, project_name, name, phone, email, txn_id, amount, created_at) VALUES (?, ?, ?, ?, ?, ?, 4999, ?)`,
    [plot_no, project_name || 'Walke Farm World', name, phone, email, txn_id, timestamp],
    function (err) {
      if (err) return res.status(500).json({ status: 'error', message: err.message });
      res.json({ status: 'success', id: this.lastID, timestamp });
    }
  );
});

// 4. Admin Get Hold Payments List
app.get('/api/admin/plot-holds', authenticateAdmin, (req, res) => {
  db.all("SELECT * FROM plot_holds ORDER BY id DESC", [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

// 5. Admin Download Hold Payments as Excel (CSV)
app.get('/api/admin/export-holds-excel', (req, res) => {
  db.all("SELECT * FROM plot_holds ORDER BY id DESC", [], (err, rows) => {
    if (err) return res.status(500).send("Error generating file.");

    let csv = "Receipt ID,Date & Time,Project,Plot No,Customer Name,Phone,Email,UTR / Transaction ID,Amount Paid,Hold Status\n";
    rows.forEach(r => {
      csv += `"WFW-HOLD-${r.id}","${r.created_at}","${r.project_name}","${r.plot_no}","${r.name}","${r.phone}","${r.email}","${r.txn_id}","₹${r.amount}","${r.status}"\n`;
    });

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="WalkeFarm_Plot_Hold_Payments.csv"');
    res.status(200).send(csv);
  });
});

// 6. Admin Get Enquiries
app.get('/api/admin/enquiries', authenticateAdmin, (req, res) => {
  db.all("SELECT * FROM enquiries ORDER BY id DESC", [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

// 7. Admin Update Lead Status
app.post('/api/admin/update-lead-status', authenticateAdmin, (req, res) => {
  const { id, status } = req.body;
  db.run("UPDATE enquiries SET status = ? WHERE id = ?", [status, id], function(err) {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ status: 'success' });
  });
});

// 8. Admin Export Enquiries CSV
app.get('/api/admin/export-csv', (req, res) => {
  db.all("SELECT * FROM enquiries ORDER BY id DESC", [], (err, rows) => {
    if (err) return res.status(500).send("Error generating file.");

    let csv = "ID,Name,Phone,Project,Plot Details,Preferred Date,Status,Created At\n";
    rows.forEach(r => {
      csv += `"${r.id}","${r.name}","${r.phone}","${r.project_name}","${r.plot_size}","${r.visit_date}","${r.status}","${r.created_at}"\n`;
    });

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="WalkeFarm_Leads_CRM.csv"');
    res.status(200).send(csv);
  });
});

// 9. Admin Get Plots Grid
app.get('/api/admin/plots', authenticateAdmin, (req, res) => {
  db.all("SELECT * FROM plots ORDER BY id ASC", [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

// 10. Admin Update Plot Status
app.post('/api/admin/update-plot-status', authenticateAdmin, (req, res) => {
  const { id, status } = req.body;
  db.run("UPDATE plots SET status = ? WHERE id = ?", [status, id], function(err) {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ status: 'success' });
  });
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));