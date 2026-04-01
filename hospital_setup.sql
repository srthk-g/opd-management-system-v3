-- ============================================================
--  SILVER LOTUS HOSPITAL — Full DB Reset & Seed Script v2
--  Run in DB Browser for SQLite:
--  File > Open hospital.db → Execute SQL tab → paste → Run All
-- ============================================================


-- ------------------------------------------------------------
-- STEP 1: Drop all tables (safe order for foreign keys)
-- ------------------------------------------------------------

DROP TABLE IF EXISTS visits;
DROP TABLE IF EXISTS bed_bookings;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS inventory_managers;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS beds;


-- ------------------------------------------------------------
-- STEP 2: Create tables
-- ------------------------------------------------------------

CREATE TABLE patients (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    phone         TEXT    NOT NULL UNIQUE,
    password      TEXT    NOT NULL
);

CREATE TABLE doctors (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id     TEXT    NOT NULL UNIQUE,   -- login ID e.g. DOC001
    name          TEXT    NOT NULL,
    specialty     TEXT    NOT NULL,
    password      TEXT    NOT NULL,
    available     INTEGER NOT NULL DEFAULT 1  -- 1=available, 0=unavailable
);

CREATE TABLE appointments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER NOT NULL REFERENCES patients(id),
    doctor_id     INTEGER NOT NULL REFERENCES doctors(id),
    date          TEXT    NOT NULL,           -- YYYY-MM-DD
    time          TEXT    NOT NULL            -- HH:MM
);

CREATE TABLE bed_bookings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER NOT NULL REFERENCES patients(id),
    ward          TEXT    NOT NULL DEFAULT 'General',
    admission_date TEXT   NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'Active'  -- 'Active' | 'Discharged'
);

CREATE TABLE inventory (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    quantity      INTEGER NOT NULL DEFAULT 0,
    unit          TEXT    NOT NULL DEFAULT 'units',
    status        TEXT    NOT NULL DEFAULT 'In Stock'
    -- status rule: qty=0 → 'Out of Stock' | qty<=30 → 'Low Stock' | else → 'In Stock'
);

CREATE TABLE visits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id     INTEGER NOT NULL REFERENCES doctors(id),
    patient_id    INTEGER NOT NULL REFERENCES patients(id),
    visit_date    TEXT    NOT NULL,           -- YYYY-MM-DD
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


-- ------------------------------------------------------------
-- STEP 3: Beds
-- ------------------------------------------------------------

INSERT INTO beds (total, available) VALUES (150, 120);


-- ------------------------------------------------------------
-- STEP 4: Doctors
-- doctor_id is used for login (not name).
-- All passwords = Doctor@123
-- SHA-256("Doctor@123") = 63bbe564aa5c0882355f6dcd6f2241b6f8d02d6f39725966ae564cd310f07850
-- ------------------------------------------------------------

INSERT INTO doctors (doctor_id, name, specialty, password, available) VALUES
    ('DOC001', 'Dr. Anjali Sharma', 'General Medicine', '63bbe564aa5c0882355f6dcd6f2241b6f8d02d6f39725966ae564cd310f07850', 1),
    ('DOC002', 'Dr. Ramesh Patel',  'Cardiology',       '63bbe564aa5c0882355f6dcd6f2241b6f8d02d6f39725966ae564cd310f07850', 1),
    ('DOC003', 'Dr. Priya Rao',     'Gynaecology',      '63bbe564aa5c0882355f6dcd6f2241b6f8d02d6f39725966ae564cd310f07850', 1),
    ('DOC004', 'Dr. Imran Khan',    'Orthopaedics',     '63bbe564aa5c0882355f6dcd6f2241b6f8d02d6f39725966ae564cd310f07850', 0),
    ('DOC005', 'Dr. Sunita Mehta',  'Paediatrics',      '63bbe564aa5c0882355f6dcd6f2241b6f8d02d6f39725966ae564cd310f07850', 1);


-- ------------------------------------------------------------
-- STEP 5: Patients
-- All passwords = Patient@123
-- SHA-256("Patient@123") = 6dff47814e92e3a14c9f021d2d3ddd353a03e5bf3b0f49d53e80a1a3606c86d6
-- ------------------------------------------------------------

INSERT INTO patients (name, phone, password) VALUES
    ('Ravi Kumar',    '9876543210', '6dff47814e92e3a14c9f021d2d3ddd353a03e5bf3b0f49d53e80a1a3606c86d6'),
    ('Meena Desai',   '9823456781', '6dff47814e92e3a14c9f021d2d3ddd353a03e5bf3b0f49d53e80a1a3606c86d6'),
    ('Suresh Nair',   '9712345678', '6dff47814e92e3a14c9f021d2d3ddd353a03e5bf3b0f49d53e80a1a3606c86d6'),
    ('Fatima Sheikh', '9634512378', '6dff47814e92e3a14c9f021d2d3ddd353a03e5bf3b0f49d53e80a1a3606c86d6'),
    ('Arjun Verma',   '9501234567', '6dff47814e92e3a14c9f021d2d3ddd353a03e5bf3b0f49d53e80a1a3606c86d6');


-- ------------------------------------------------------------
-- STEP 6: Appointments
-- ------------------------------------------------------------

INSERT INTO appointments (patient_id, doctor_id, date, time) VALUES
    (1, 1, '2026-04-05', '10:00'),
    (2, 2, '2026-04-05', '11:30'),
    (3, 3, '2026-04-06', '09:15'),
    (4, 1, '2026-04-07', '14:00'),
    (5, 5, '2026-04-08', '16:45');


-- ------------------------------------------------------------
-- STEP 7: Bed Bookings (sample admitted patient)
-- ------------------------------------------------------------

INSERT INTO bed_bookings (patient_id, ward, admission_date, status) VALUES
    (1, 'General',     '2026-04-03', 'Active'),
    (3, 'Semi-Private','2026-04-04', 'Active');

-- Reflect these 2 bookings in available beds (120 - 2 = 118)
UPDATE beds SET available = 118;


-- ------------------------------------------------------------
-- STEP 8: Inventory
-- qty=0 → Out of Stock | qty<=30 → Low Stock | else → In Stock
-- ------------------------------------------------------------

INSERT INTO inventory (name, quantity, unit, status) VALUES
    ('Paracetamol 500mg',    250, 'tablets',  'In Stock'),
    ('Amoxicillin 250mg',     18, 'capsules', 'Low Stock'),
    ('Insulin (Regular)',      0, 'vials',    'Out of Stock'),
    ('Metformin 500mg',      120, 'tablets',  'In Stock'),
    ('Omeprazole 20mg',       90, 'capsules', 'In Stock'),
    ('Aspirin 75mg',          25, 'tablets',  'Low Stock'),
    ('IV Saline 500ml',       60, 'bags',     'In Stock'),
    ('Surgical Gloves (M)',  200, 'pairs',    'In Stock'),
    ('Surgical Masks',       500, 'units',    'In Stock'),
    ('Syringes 5ml',          12, 'units',    'Low Stock'),
    ('Betadine Solution',      0, 'bottles',  'Out of Stock'),
    ('Ringer Lactate 500ml',  45, 'bags',     'In Stock');


-- ------------------------------------------------------------
-- STEP 9: Inventory Managers
-- All passwords = Admin@123
-- SHA-256("Admin@123") = e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7
-- ------------------------------------------------------------

INSERT INTO inventory_managers (manager_id, password) VALUES
    ('admin',       'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7'),
    ('inventory1',  'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7');


-- ------------------------------------------------------------
-- STEP 10: Verification — should show row counts for all tables
-- ------------------------------------------------------------

SELECT 'patients'           AS table_name, COUNT(*) AS rows FROM patients
UNION ALL
SELECT 'doctors',                           COUNT(*)         FROM doctors
UNION ALL
SELECT 'appointments',                      COUNT(*)         FROM appointments
UNION ALL
SELECT 'visits',                            COUNT(*)         FROM visits
UNION ALL
SELECT 'bed_bookings',                      COUNT(*)         FROM bed_bookings
UNION ALL
SELECT 'inventory',                         COUNT(*)         FROM inventory
UNION ALL
SELECT 'inventory_managers',                COUNT(*)         FROM inventory_managers
UNION ALL
SELECT 'beds',                              COUNT(*)         FROM beds;
