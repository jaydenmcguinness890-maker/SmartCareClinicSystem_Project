import os
import tempfile

import pytest

from app import create_app


@pytest.fixture()
def client():
    handle, path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": path, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client
    os.close(handle)
    os.unlink(path)


def login(client):
    return client.post("/login", data={"username": "admin", "password": "SmartCare123!"})


def test_login_requires_correct_password(client):
    response = client.post("/login", data={"username": "admin", "password": "wrong"})
    assert b"Invalid username or password" in response.data
    assert login(client).status_code == 302


def test_patient_registration_and_duplicate_validation(client):
    login(client)
    patient = {"patient_number": "12345678", "first_name": "Thandi", "last_name": "Khumalo",
               "id_number": "0601011234088", "date_of_birth": "2006-01-01", "gender": "Female",
               "contact_number": "0821234567", "email": "thandi@example.com",
               "residential_address": "12 Main Road", "emergency_contact": "Lindi Khumalo"}
    response = client.post("/patients/new", data=patient, follow_redirects=True)
    assert b"Patient registered successfully" in response.data
    response = client.post("/patients/new", data=patient, follow_redirects=True)
    assert b"already exists" in response.data


def test_dashboard_is_protected(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_appointment_booking_and_double_booking_prevention(client):
    login(client)
    patient = {"patient_number": "87654321", "first_name": "Sipho", "last_name": "Nkosi",
               "id_number": "0502025678081", "date_of_birth": "2005-02-02", "gender": "Male",
               "contact_number": "0831234567", "email": "sipho@example.com",
               "residential_address": "8 Clinic Street", "emergency_contact": "Zanele Nkosi"}
    client.post("/patients/new", data=patient)
    appointment = {"appointment_number": "APT-1001", "patient_id": "1", "doctor_id": "1",
                   "appointment_date": "2030-05-10", "appointment_time": "10:00",
                   "status": "Scheduled", "notes": "General consultation"}
    response = client.post("/appointments/new", data=appointment, follow_redirects=True)
    assert b"Appointment booked successfully" in response.data
    appointment["appointment_number"] = "APT-1002"
    response = client.post("/appointments/new", data=appointment, follow_redirects=True)
    assert b"already booked" in response.data
