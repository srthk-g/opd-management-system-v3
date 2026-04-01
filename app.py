from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "opd_secret_key_change_in_prod")

# Always resolve DB relative to current working directory (where gunicorn is launched)
DB_PATH = os.path.join(os.getcwd(), "hospital.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def compute_status(qty):
    if qty == 0:
        return "Out of Stock"
    elif qty <= 30:
        return "Low Stock"
    else:
        return "In Stock"


# ── Home ─────────────────────────────────────────────────

@app.route("/")
def home():
    db = get_db()
    beds_row = db.execute("SELECT total, available FROM beds").fetchone()
    beds = beds_row["available"] if beds_row else 0
    doctor_count = db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    doctors = db.execute(
        "SELECT id, name, specialty FROM doctors WHERE available=1"
    ).fetchall()
    db.close()
    return render_template("index.html", beds=beds, doctor_count=doctor_count, doctors=doctors)


# ── Patient ──────────────────────────────────────────────

@app.route("/register/patient", methods=["GET", "POST"])
def register_patient():
    error = None
    if request.method == "POST":
        db = get_db()
        try:
            db.execute(
                "INSERT INTO patients (name, phone, password) VALUES (?, ?, ?)",
                (request.form["name"], request.form["phone"], hash_password(request.form["password"]))
            )
            db.commit()
            db.close()
            return redirect(url_for("login_patient"))
        except sqlite3.IntegrityError:
            error = "Phone number already registered."
        db.close()
    return render_template("register_patient.html", error=error)


@app.route("/login/patient", methods=["GET", "POST"])
def login_patient():
    error = None
    if request.method == "POST":
        db = get_db()
        user = db.execute(
            "SELECT * FROM patients WHERE phone=? AND password=?",
            (request.form["phone"], hash_password(request.form["password"]))
        ).fetchone()
        db.close()
        if user:
            session["patient_id"] = user["id"]
            session["patient_name"] = user["name"]
            return redirect(url_for("patient_dashboard"))
        error = "Invalid phone number or password."
    return render_template("login_patient.html", error=error)


@app.route("/patient/dashboard")
def patient_dashboard():
    if "patient_id" not in session:
        return redirect(url_for("login_patient"))
    db = get_db()
    doctors = db.execute(
        "SELECT id, name, specialty FROM doctors WHERE available=1"
    ).fetchall()
    beds_row = db.execute("SELECT total, available FROM beds").fetchone()
    total_beds = beds_row["total"] if beds_row else 0
    available_beds = beds_row["available"] if beds_row else 0
    existing_booking = db.execute(
        "SELECT * FROM bed_bookings WHERE patient_id=? AND status='Active'",
        (session["patient_id"],)
    ).fetchone()
    db.close()
    return render_template(
        "patient_dashboard.html",
        doctors=doctors,
        total_beds=total_beds,
        available_beds=available_beds,
        existing_booking=existing_booking
    )


# ── Bed Booking ──────────────────────────────────────────

@app.route("/bed/book", methods=["POST"])
def bed_book():
    if "patient_id" not in session:
        return redirect(url_for("login_patient"))
    db = get_db()
    existing = db.execute(
        "SELECT * FROM bed_bookings WHERE patient_id=? AND status='Active'",
        (session["patient_id"],)
    ).fetchone()
    if existing:
        db.close()
        return redirect(url_for("patient_dashboard"))
    beds_row = db.execute("SELECT available FROM beds").fetchone()
    if not beds_row or beds_row["available"] <= 0:
        db.close()
        return render_template("bed_confirmation.html", success=False,
                               message="No beds available at this time.")
    ward = request.form.get("ward", "General")
    admission_date = request.form.get("admission_date", "")
    db.execute(
        "INSERT INTO bed_bookings (patient_id, ward, admission_date, status) VALUES (?, ?, ?, 'Active')",
        (session["patient_id"], ward, admission_date)
    )
    db.execute("UPDATE beds SET available = available - 1")
    db.commit()
    db.close()
    return render_template("bed_confirmation.html", success=True,
                           message="Bed booked successfully!",
                           ward=ward, admission_date=admission_date)


# ── Doctor ───────────────────────────────────────────────

@app.route("/register/doctor", methods=["GET", "POST"])
def register_doctor():
    error = None
    if request.method == "POST":
        db = get_db()
        try:
            db.execute(
                "INSERT INTO doctors (doctor_id, name, specialty, password, available) VALUES (?, ?, ?, ?, 1)",
                (request.form["doctor_id"], request.form["name"],
                 request.form["specialty"], hash_password(request.form["password"]))
            )
            db.commit()
            db.close()
            return redirect(url_for("login_doctor"))
        except sqlite3.IntegrityError:
            error = "Doctor ID already exists."
        db.close()
    return render_template("register_doctor.html", error=error)


@app.route("/login/doctor", methods=["GET", "POST"])
def login_doctor():
    error = None
    if request.method == "POST":
        db = get_db()
        doctor = db.execute(
            "SELECT * FROM doctors WHERE doctor_id=? AND password=?",
            (request.form["doctor_id"], hash_password(request.form["password"]))
        ).fetchone()
        db.close()
        if doctor:
            session["doctor_id"] = doctor["id"]
            session["doctor_name"] = doctor["name"]
            return redirect(url_for("doctor_dashboard"))
        error = "Invalid Doctor ID or password."
    return render_template("login_doctor.html", error=error)


@app.route("/doctor/dashboard")
def doctor_dashboard():
    if "doctor_id" not in session:
        return redirect(url_for("login_doctor"))
    db = get_db()
    appointments = db.execute(
        """SELECT p.name, a.date, a.time
           FROM appointments a
           JOIN patients p ON a.patient_id=p.id
           WHERE a.doctor_id=?
           ORDER BY a.date, a.time""",
        (session["doctor_id"],)
    ).fetchall()
    doctor = db.execute(
        "SELECT available FROM doctors WHERE id=?",
        (session["doctor_id"],)
    ).fetchone()
    db.close()
    available = doctor["available"] if doctor else 0
    return render_template("doctor_dashboard.html", appointments=appointments, available=available)


# ── Doctor sub-pages ─────────────────────────────────────

@app.route("/doctor/appointments")
def doctor_appointments():
    if "doctor_id" not in session:
        return redirect(url_for("login_doctor"))
    db = get_db()
    appointments = db.execute(
        """SELECT p.name, a.date, a.time
           FROM appointments a
           JOIN patients p ON a.patient_id=p.id
           WHERE a.doctor_id=?
           ORDER BY a.date, a.time""",
        (session["doctor_id"],)
    ).fetchall()
    db.close()
    return render_template("doctor_appointments.html", appointments=appointments)


@app.route("/doctor/add-visit", methods=["GET", "POST"])
def doctor_add_visit():
    if "doctor_id" not in session:
        return redirect(url_for("login_doctor"))
    db = get_db()
    saved = None
    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        visit_date = request.form.get("visit_date")
        diagnosis  = request.form.get("diagnosis", "").strip()
        notes      = request.form.get("notes", "").strip()
        db.execute(
            "INSERT INTO visits (doctor_id, patient_id, visit_date, diagnosis, notes) VALUES (?,?,?,?,?)",
            (session["doctor_id"], patient_id, visit_date, diagnosis, notes)
        )
        db.commit()
        patient = db.execute("SELECT name FROM patients WHERE id=?", (patient_id,)).fetchone()
        saved = patient["name"] if patient else "Patient"
    patients = db.execute("SELECT id, name, phone FROM patients ORDER BY name").fetchall()
    db.close()
    return render_template("doctor_add_visit.html", patients=patients, saved=saved)


@app.route("/doctor/patient-records")
def doctor_patient_records():
    if "doctor_id" not in session:
        return redirect(url_for("login_doctor"))
    db = get_db()
    records = db.execute(
        """SELECT p.name AS patient_name, v.visit_date, v.diagnosis, v.notes
           FROM visits v
           JOIN patients p ON v.patient_id=p.id
           WHERE v.doctor_id=?
           ORDER BY v.visit_date DESC""",
        (session["doctor_id"],)
    ).fetchall()
    db.close()
    return render_template("doctor_patient_records.html", records=records)


@app.route("/doctor/toggle-availability", methods=["POST"])
def toggle_availability():
    if "doctor_id" not in session:
        return redirect(url_for("login_doctor"))
    # Read the desired new value sent explicitly from the form
    new_value = int(request.form.get("new_value", 1))
    db = get_db()
    db.execute(
        "UPDATE doctors SET available=? WHERE id=?",
        (new_value, session["doctor_id"])
    )
    db.commit()
    db.close()
    return redirect(url_for("doctor_dashboard"))


# ── Appointments ─────────────────────────────────────────

@app.route("/book", methods=["POST"])
def book():
    if "patient_id" not in session:
        return redirect(url_for("login_patient"))
    db = get_db()
    db.execute(
        "INSERT INTO appointments (patient_id, doctor_id, date, time) VALUES (?, ?, ?, ?)",
        (session["patient_id"], request.form["doctor"], request.form["date"], request.form["time"])
    )
    db.commit()
    db.close()
    return render_template("confirmation.html")


# ── Inventory ────────────────────────────────────────────

@app.route("/login/inventory", methods=["GET", "POST"])
def login_inventory():
    error = None
    if request.method == "POST":
        db = get_db()
        manager = db.execute(
            "SELECT * FROM inventory_managers WHERE manager_id=? AND password=?",
            (request.form["manager_id"], hash_password(request.form["password"]))
        ).fetchone()
        db.close()
        if manager:
            session["inventory_manager"] = True
            session["manager_id"] = request.form["manager_id"]
            return redirect(url_for("inventory"))
        error = "Invalid Manager ID or password."
    return render_template("inventory_manager.html", error=error)


@app.route("/inventory")
def inventory():
    if not session.get("inventory_manager"):
        return redirect(url_for("login_inventory"))
    db = get_db()
    items = db.execute("SELECT id, name, quantity, unit, status FROM inventory ORDER BY name").fetchall()
    db.close()
    return render_template("inventory.html", items=items)


@app.route("/inventory/add", methods=["POST"])
def inventory_add():
    if not session.get("inventory_manager"):
        return redirect(url_for("login_inventory"))
    name     = request.form.get("name", "").strip()
    quantity = int(request.form.get("quantity", 0))
    unit     = request.form.get("unit", "units").strip()
    status   = compute_status(quantity)
    if name:
        db = get_db()
        db.execute(
            "INSERT INTO inventory (name, quantity, unit, status) VALUES (?, ?, ?, ?)",
            (name, quantity, unit, status)
        )
        db.commit()
        db.close()
    return redirect(url_for("inventory"))


# ── Logout ───────────────────────────────────────────────

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=False)
