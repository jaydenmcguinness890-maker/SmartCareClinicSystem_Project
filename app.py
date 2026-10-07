import os
import sqlite3
from datetime import date
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = get_db()
        with app.open_resource("schema.sql") as schema:
            db.executescript(schema.read().decode("utf8"))
        if not db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            db.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                ("admin", generate_password_hash("SmartCare123!"), "System Administrator", "Administrator"),
            )
        if not db.execute("SELECT 1 FROM doctors LIMIT 1").fetchone():
            db.executemany(
                "INSERT INTO doctors (full_name, specialisation, phone_number, email) VALUES (?, ?, ?, ?)",
                [
                    ("Dr Naledi Mokoena", "General Practitioner", "0115550101", "naledi@smartcare.co.za"),
                    ("Dr Liam Naidoo", "Paediatrics", "0115550102", "liam@smartcare.co.za"),
                    ("Dr Ayanda Dlamini", "Internal Medicine", "0115550103", "ayanda@smartcare.co.za"),
                ],
            )
        db.commit()

    def login_required(view):
        @wraps(view)
        def wrapped(**kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))
            return view(**kwargs)
        return wrapped

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("SmartCare database initialised.")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["user_id"]
                session["full_name"] = user["full_name"]
                flash("Welcome back to SmartCare.", "success")
                return redirect(url_for("dashboard"))
            flash("Invalid username or password.", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def dashboard():
        db = get_db()
        totals = {
            "patients": db.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
            "doctors": db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
            "appointments": db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
            "upcoming": db.execute(
                "SELECT COUNT(*) FROM appointments WHERE appointment_date >= ? AND status IN ('Scheduled','Confirmed')",
                (date.today().isoformat(),),
            ).fetchone()[0],
        }
        appointments = db.execute(
            """SELECT a.*, p.patient_number, p.first_name || ' ' || p.last_name AS patient_name,
                      d.full_name AS doctor_name
               FROM appointments a JOIN patients p ON p.patient_id=a.patient_id
               JOIN doctors d ON d.doctor_id=a.doctor_id
               ORDER BY a.appointment_date, a.appointment_time LIMIT 10"""
        ).fetchall()
        return render_template("dashboard.html", totals=totals, appointments=appointments)

    def validate_patient(form):
        required = ["patient_number", "first_name", "last_name", "id_number", "date_of_birth",
                    "gender", "contact_number", "email", "residential_address", "emergency_contact"]
        if any(not form.get(field, "").strip() for field in required):
            return "Please complete all required fields."
        if not (form["patient_number"].isdigit() and len(form["patient_number"]) == 8):
            return "Patient number must contain exactly 8 digits."
        if not (form["id_number"].isdigit() and len(form["id_number"]) == 13):
            return "South African ID number must contain exactly 13 digits."
        if "@" not in form["email"]:
            return "Please enter a valid email address."
        return None

    @app.route("/patients")
    @login_required
    def patients():
        query = request.args.get("q", "").strip()
        db = get_db()
        if query:
            rows = db.execute(
                """SELECT * FROM patients WHERE patient_number LIKE ? OR first_name LIKE ?
                   OR last_name LIKE ? OR id_number LIKE ? ORDER BY last_name, first_name""",
                tuple([f"%{query}%"] * 4),
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM patients ORDER BY last_name, first_name").fetchall()
        return render_template("patients.html", patients=rows, query=query)

    @app.route("/patients/new", methods=["GET", "POST"])
    @login_required
    def register_patient():
        if request.method == "POST":
            error = validate_patient(request.form)
            if not error:
                fields = ["patient_number", "first_name", "last_name", "id_number", "date_of_birth",
                          "gender", "contact_number", "email", "residential_address", "medical_aid_provider",
                          "medical_aid_number", "emergency_contact", "emergency_contact_phone", "blood_type",
                          "allergies", "chronic_conditions", "preferred_language", "next_of_kin_relationship"]
                values = [request.form.get(f, "").strip() or None for f in fields]
                try:
                    get_db().execute(
                        f"INSERT INTO patients ({','.join(fields)}) VALUES ({','.join(['?'] * len(fields))})", values
                    )
                    get_db().commit()
                    flash("Patient registered successfully.", "success")
                    return redirect(url_for("patients"))
                except sqlite3.IntegrityError:
                    error = "Patient number or ID number already exists."
            flash(error, "danger")
        return render_template("patient_form.html", patient=None)

    @app.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_patient(patient_id):
        db = get_db()
        patient = db.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,)).fetchone()
        if not patient:
            flash("Patient not found.", "danger")
            return redirect(url_for("patients"))
        if request.method == "POST":
            error = validate_patient(request.form)
            if not error:
                fields = ["patient_number", "first_name", "last_name", "id_number", "date_of_birth", "gender",
                          "contact_number", "email", "residential_address", "medical_aid_provider", "medical_aid_number",
                          "emergency_contact", "emergency_contact_phone", "blood_type", "allergies",
                          "chronic_conditions", "preferred_language", "next_of_kin_relationship"]
                values = [request.form.get(f, "").strip() or None for f in fields] + [patient_id]
                try:
                    db.execute(f"UPDATE patients SET {','.join(f'{f}=?' for f in fields)} WHERE patient_id=?", values)
                    db.commit()
                    flash("Patient information updated.", "success")
                    return redirect(url_for("patients"))
                except sqlite3.IntegrityError:
                    error = "Patient number or ID number already belongs to another patient."
            flash(error, "danger")
        return render_template("patient_form.html", patient=patient)

    @app.route("/doctors")
    @login_required
    def doctors():
        rows = get_db().execute("SELECT * FROM doctors ORDER BY full_name").fetchall()
        return render_template("doctors.html", doctors=rows)

    @app.route("/appointments")
    @login_required
    def appointments():
        rows = get_db().execute(
            """SELECT a.*, p.patient_number, p.first_name || ' ' || p.last_name AS patient_name,
                      d.full_name AS doctor_name FROM appointments a
               JOIN patients p ON p.patient_id=a.patient_id JOIN doctors d ON d.doctor_id=a.doctor_id
               ORDER BY a.appointment_date DESC, a.appointment_time DESC"""
        ).fetchall()
        return render_template("appointments.html", appointments=rows)

    @app.route("/appointments/new", methods=["GET", "POST"])
    @login_required
    def book_appointment():
        db = get_db()
        if request.method == "POST":
            values = [request.form.get(k, "").strip() for k in
                      ["appointment_number", "patient_id", "doctor_id", "appointment_date", "appointment_time", "status", "notes"]]
            if any(not v for v in values[:6]):
                flash("Please complete all required appointment fields.", "danger")
            else:
                try:
                    db.execute("""INSERT INTO appointments
                        (appointment_number, patient_id, doctor_id, appointment_date, appointment_time, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""", values)
                    db.commit()
                    flash("Appointment booked successfully.", "success")
                    return redirect(url_for("appointments"))
                except sqlite3.IntegrityError as exc:
                    message = "That doctor is already booked at this date and time."
                    if "appointment_number" in str(exc):
                        message = "Appointment number already exists."
                    flash(message, "danger")
        return render_template("appointment_form.html",
                               patients=db.execute("SELECT * FROM patients ORDER BY last_name").fetchall(),
                               doctors=db.execute("SELECT * FROM doctors ORDER BY full_name").fetchall(),
                               today=date.today().isoformat())

    @app.route("/appointments/<int:appointment_id>/status", methods=["POST"])
    @login_required
    def update_appointment_status(appointment_id):
        status = request.form.get("status")
        if status not in {"Scheduled", "Confirmed", "Completed", "Cancelled", "No-show"}:
            flash("Invalid appointment status.", "danger")
        else:
            get_db().execute("UPDATE appointments SET status=? WHERE appointment_id=?", (status, appointment_id))
            get_db().commit()
            flash("Appointment status updated.", "success")
        return redirect(url_for("appointments"))

    with app.app_context():
        init_db()
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

