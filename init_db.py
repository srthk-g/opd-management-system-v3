"""
Run once on first deploy to create and seed the database.
render.yaml buildCommand calls this automatically.
"""
import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "hospital.db")

def h(p):
    return hashlib.sha256(p.encode()).hexdigest()

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.executescript("""
CREATE TABLE patients (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    phone         TEXT    NOT NULL UNIQUE,
    password      TEXT    NOT NULL
);

CREATE TABLE doctors (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id     TEXT    NOT NULL UNIQUE,
    name          TEXT    NOT NULL,
    specialty     TEXT    NOT NULL,
    password      TEXT    NOT NULL,
    available     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE appointments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER NOT NULL REFERENCES patients(id),
    doctor_id     INTEGER NOT NULL REFERENCES doctors(id),
    date          TEXT    NOT NULL,
    time          TEXT    NOT NULL
);

CREATE TABLE bed_bookings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER NOT NULL REFERENCES patients(id),
    ward          TEXT    NOT NULL DEFAULT 'General',
    admission_date TEXT   NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'Active'
);

CREATE TABLE inventory (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    quantity      INTEGER NOT NULL DEFAULT 0,
    unit          TEXT    NOT NULL DEFAULT 'units',
    status        TEXT    NOT NULL DEFAULT 'In Stock'
);

CREATE TABLE visits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id     INTEGER NOT NULL REFERENCES doctors(id),
    patient_id    INTEGER NOT NULL REFERENCES patients(id),
    visit_date    TEXT    NOT NULL,
    diagnosis     TEXT    NOT NULL,
    notes         TEXT
);

CREATE TABLE inventory_managers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    manager_id    TEXT    NOT NULL UNIQUE,
    password      TEXT    NOT NULL
);

CREATE TABLE beds (
    total         INTEGER NOT NULL,
    available     INTEGER NOT NULL
);
""")

c.execute("INSERT INTO beds VALUES (150, 120)")

# Seed doctors (login: DOC001–DOC005 / Doctor@123)
doc_pw = h("Doctor@123")
c.executemany(
    "INSERT INTO doctors (doctor_id, name, specialty, password, available) VALUES (?,?,?,?,?)",
    [
        ("DOC001", "Dr. Anjali Sharma", "General Medicine", doc_pw, 1),
        ("DOC002", "Dr. Ramesh Patel",  "Cardiology",       doc_pw, 1),
        ("DOC003", "Dr. Priya Rao",     "Gynaecology",      doc_pw, 1),
        ("DOC004", "Dr. Imran Khan",    "Orthopaedics",     doc_pw, 0),
        ("DOC005", "Dr. Sunita Mehta",  "Paediatrics",      doc_pw, 1),
    ]
)

# Seed patients (login: phone / Patient@123)
pat_pw = h("Patient@123")
c.executemany(
    "INSERT INTO patients (name, phone, password) VALUES (?,?,?)",
    [
        ("Ravi Kumar",    "9876543210", pat_pw),
        ("Meena Desai",   "9823456781", pat_pw),
        ("Suresh Nair",   "9712345678", pat_pw),
        ("Fatima Sheikh", "9634512378", pat_pw),
        ("Arjun Verma",   "9501234567", pat_pw),
    ]
)

# Seed appointments
c.executemany(
    "INSERT INTO appointments (patient_id, doctor_id, date, time) VALUES (?,?,?,?)",
    [
        (1, 1, "2026-04-05", "10:00"),
        (2, 2, "2026-04-05", "11:30"),
        (3, 3, "2026-04-06", "09:15"),
        (4, 1, "2026-04-07", "14:00"),
        (5, 5, "2026-04-08", "16:45"),
    ]
)

# Seed inventory
c.executemany(
    "INSERT INTO inventory (name, quantity, unit, status) VALUES (?,?,?,?)",
    [
        ("Paracetamol 500mg",   250, "tablets",  "In Stock"),
        ("Amoxicillin 250mg",    18, "capsules", "Low Stock"),
        ("Insulin (Regular)",     0, "vials",    "Out of Stock"),
        ("Metformin 500mg",     120, "tablets",  "In Stock"),
        ("Omeprazole 20mg",      90, "capsules", "In Stock"),
        ("Aspirin 75mg",         25, "tablets",  "Low Stock"),
        ("IV Saline 500ml",      60, "bags",     "In Stock"),
        ("Surgical Gloves (M)", 200, "pairs",    "In Stock"),
        ("Surgical Masks",      500, "units",    "In Stock"),
        ("Syringes 5ml",         12, "units",    "Low Stock"),
        ("Betadine Solution",     0, "bottles",  "Out of Stock"),
        ("Ringer Lactate 500ml", 45, "bags",     "In Stock"),
    ]
)

# Seed inventory managers (login: admin or inventory1 / Admin@123)
adm_pw = h("Admin@123")
c.executemany(
    "INSERT INTO inventory_managers (manager_id, password) VALUES (?,?)",
    [("admin", adm_pw), ("inventory1", adm_pw)]
)

conn.commit()
conn.close()
print("Database initialised successfully.")
