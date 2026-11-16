# Fleet Telematics System for Vehicle Tracking and Management
University of Ibadan case study | CSC 476, Group 67

Prototype of the system designed in the project report: GPS pings are received over a REST endpoint,
trips are opened and closed automatically, geofence and over-speeding alerts are raised, and utilization
reports are generated on demand. Built with Django; SQLite by default, MySQL supported.

## Features
- `POST /api/telemetry` receives GPS pings from a tracker (Figure 3.5, messages 1-4)
- Automatic trip logging: distance (haversine), duration, average speed
- Geofence and over-speeding alerts
- Live map dashboard (Leaflet) with auto-refresh
- Utilization report (daily/weekly/monthly) using the logic in Appendix B; print to PDF
- Role-based access through Django login and admin

## Setup
```bash
python -m venv venv
venv\Scripts\activate            # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python manage.py makemigrations tracker
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in. In a second terminal run the simulated tracker:
```bash
python simulate_gps.py
```
Refresh the dashboard to see the vehicle, the alerts, and then open **Reports**.

## Using MySQL (as in the report)
Install `mysqlclient`, create a database, then set `DB_ENGINE=mysql`, `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, `DB_HOST` as environment variables before running migrate.

## Tests
`python manage.py test tracker`

## Project structure
- `tracker/models.py` database tables (Chapter 3, Tables 3.1-3.6)
- `tracker/services.py` trip logging and alert rules
- `tracker/utils.py` distance, geofence and utilization calculations
- `tracker/views.py` telemetry API, dashboard, report
- `simulate_gps.py` stand-in for the GPS/GSM unit
