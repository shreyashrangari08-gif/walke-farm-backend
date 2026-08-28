import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS projects')
    cursor.execute('DROP TABLE IF EXISTS plots')
    cursor.execute('DROP TABLE IF EXISTS enquiries')

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Projects Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            tagline TEXT,
            total_area TEXT,
            amenities_area TEXT,
            rate_per_sqft TEXT,
            emi_offer TEXT,
            location_url TEXT,
            cover_image TEXT,
            description TEXT
        )
    ''')

    # Plots Table with Real-Time Booking Status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_slug TEXT NOT NULL,
            size TEXT NOT NULL,
            total_price TEXT NOT NULL,
            down_payment TEXT NOT NULL,
            emi_plan TEXT NOT NULL,
            features TEXT,
            status TEXT NOT NULL DEFAULT 'Available',
            image_url TEXT
        )
    ''')

    # Enquiries Table with Lead Status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            project_name TEXT,
            plot_size TEXT,
            visit_date TEXT,
            message TEXT,
            status TEXT NOT NULL DEFAULT 'New Lead',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Encrypted Dual Admins
    hashed_pwd = generate_password_hash("Shreyash@0222")
    admins = [
        ("shreyashrangari08@gmail.com", hashed_pwd, "admin"),
        ("Soniyasheikh594@gmail.com", hashed_pwd, "admin")
    ]
    cursor.executemany("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", admins)

    # 1. Project: Degma Farmland
    cursor.execute('''
        INSERT INTO projects (slug, name, tagline, total_area, amenities_area, rate_per_sqft, emi_offer, location_url, cover_image, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "degma", "Degma Farmland", "Live in the Heart of Nature", "122 Acres", "7 Acres Amenities",
        "₹450 / sq.ft.", "24 Months Easy EMI @ 0% Interest", "https://share.google/BMTY8avUrswvyyQX7",
        "images/farm1.jpg", "A peaceful destination nestled in nature near Bor Safari."
    ))

    # 2. Project: Strawberry Resort
    cursor.execute('''
        INSERT INTO projects (slug, name, tagline, total_area, amenities_area, rate_per_sqft, emi_offer, location_url, cover_image, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "strawberry", "Strawberry Resort (🌸 Muniya Farm 🌸)", "Farmhouse & Cottage Luxury Resort",
        "1,000 to 5,000 Sq.ft.", "36 Cottages, Pool, Machan, Restaurant", "₹1,400 / sq.ft.",
        "90% Bank Finance Available | 12M 0% EMI", "https://share.google/Cd6a0cIAjs1LdKB7L",
        "images/resort1.jpg", "Today best investment for self and family just 20km from Chhatrapati square."
    ))

    # 3. Project: Mind Game
    cursor.execute('''
        INSERT INTO projects (slug, name, tagline, total_area, amenities_area, rate_per_sqft, emi_offer, location_url, cover_image, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "mindgame", "Mind Game (Highway Touch)", "Premium Residential & Commercial Plots on S.H 262",
        "4 Acres Project", "Opposite Petrol Pump & Metro Corridor", "₹1,400 / sq.ft.",
        "Easy EMI with 0% Interest", "https://maps.google.com/?q=MH+SH+262+Butibori+Umred+Road",
        "images/mind1.jpg", "Prime highway touch property on SH 262, 6 KM from Butibori Metro Station."
    ))

    # Plots Data with Status
    plots_data = [
        ("degma", "3,000 Sq.ft.", "₹13,00,000", "₹1,00,000", "₹50,000 / Month (24M)", "Nature View Plot", "Available", "images/farm4.jpg"),
        ("degma", "6,000 Sq.ft.", "₹27,00,000", "₹3,00,000", "₹1,00,000 / Month (24M)", "Road Facing Plot", "Available", "images/farm8.jpg"),
        ("degma", "11,000 Sq.ft.", "₹49,00,000", "₹5,00,000", "₹1,83,333 / Month (24M)", "Scenic Plantation Plot", "Available", "images/farm3.jpg"),
        ("degma", "22,000 Sq.ft.", "₹99,00,000", "₹9,00,000", "₹3,75,000 / Month (24M)", "Premium Estate Land", "Available", "images/farm10.jpg"),
        
        ("strawberry", "Fully Furnished Cottage (Plot 1,114 Sq.ft.)", "₹24,00,000", "10% Down Payment", "Bank Finance Available", "300 sq.ft Construction, AC, TV, Bed, Sofa, Curtains (2 for Sale)", "Available", "images/resort5.jpg"),
        ("strawberry", "1,000 Sq.ft. Farm Plot", "₹14,00,000", "₹1,40,000", "12 Months Easy EMI / 90% Loan", "NMRDA & R1 Sanctioned Plot @ ₹1,400/sq.ft.", "Available", "images/resort8.jpg"),
        ("strawberry", "3,000 Sq.ft. Farm Plot", "₹42,00,000", "₹4,20,000", "12 Months Easy EMI / 90% Loan", "NMRDA & R1 Sanctioned Plot @ ₹1,400/sq.ft.", "Available", "images/resort7.jpg"),
        ("strawberry", "5,000 Sq.ft. Farm Plot", "₹70,00,000", "₹7,00,000", "12 Months Easy EMI / 90% Loan", "Resort Facing Large Farm Plot", "Available", "images/resort6.jpg"),

        ("mindgame", "1,000 Sq.ft. Plot", "₹14,00,000", "₹1,40,000", "Easy EMI @ 0% Interest", "NMRDA Sanctioned | Highway Touch S.H 262", "Available", "images/mind5.jpg"),
        ("mindgame", "2,000 Sq.ft. Plot", "₹28,00,000", "₹2,80,000", "Easy EMI @ 0% Interest", "Ideal for Residential Home or Shop", "Available", "images/mind6.jpg"),
        ("mindgame", "3,000 Sq.ft. Plot", "₹42,00,000", "₹4,20,000", "Easy EMI @ 0% Interest", "Semi-Commercial / Commercial Use", "Available", "images/mind3.jpg"),
        ("mindgame", "5,000 Sq.ft. Prime Commercial Plot", "₹70,00,000", "₹7,00,000", "Easy EMI @ 0% Interest", "Opposite Petrol Pump Highway Frontage", "Available", "images/mind1.jpg")
    ]

    cursor.executemany('''
        INSERT INTO plots (project_slug, size, total_price, down_payment, emi_plan, features, status, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', plots_data)

    conn.commit()
    conn.close()
    print("Database Initialized with Encrypted Passwords & Status Controls!")

if __name__ == '__main__':
    init_db()