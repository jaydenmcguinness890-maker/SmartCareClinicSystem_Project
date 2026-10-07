# SmartCare Medical Clinic Appointment Management System

SmartCare is a responsive Flask web application for registering patients, storing doctor data, securely managing users, booking appointments, preventing doctor double-bookings, maintaining appointment history and showing clinic statistics.

## Setup on Windows

1. Open PowerShell in the `SmartCare` folder.
2. Create a virtual environment: `py -m venv .venv`
3. Activate it: `.venv\Scripts\Activate.ps1`
4. Install requirements: `py -m pip install -r requirements.txt`
5. Start the application: `py app.py`
6. Open `http://127.0.0.1:5000` in Chrome or Edge.

Login with:

- Username: `admin`
- Password: `SmartCare123!`

The database and three sample doctors are created automatically on first launch.

## Run tests

Run `py -m pytest -v`. The tests cover protected pages, secure login, patient registration and duplicate-data validation.

## Security and validation

- Passwords are stored as salted hashes, never plain text.
- Parameterised SQL queries reduce SQL-injection risk.
- Sessions use HTTP-only and SameSite cookies.
- Unique constraints prevent duplicate patient numbers, ID numbers and appointment numbers.
- A composite unique constraint prevents doctors from being double-booked.
- Required-field, length and basic email validation is applied.

## Submission files

- `app.py` — Flask routes, validation and database operations
- `schema.sql` — normalised relational database schema
- `schema_sqlserver.sql` — Microsoft SQL Server 2022 version for SSMS evidence
- `templates/` — HTML pages
- `static/style.css` — responsive external CSS
- `tests/test_app.py` — automated unit/integration tests
- `SYSTEM_DOCUMENTATION.md` — feasibility, UML, database, testing, deployment and maintenance evidence
