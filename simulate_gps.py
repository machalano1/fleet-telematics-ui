"""Simulates a GPS/GSM tracker by POSTing pings to the telemetry endpoint.
Usage:  python simulate_gps.py [device_id] [base_url]
The pings use timestamps 30 s apart (sent immediately), so a whole trip can be produced in seconds."""
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

DEVICE = sys.argv[1] if len(sys.argv) > 1 else "SIM-001"
URL = (sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000") + "/api/telemetry"


def send(lat, lon, speed, ts):
    body = json.dumps({"device_id": DEVICE, "latitude": lat, "longitude": lon,
                       "speed": speed, "timestamp": ts.isoformat()}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        r.read()


t = datetime.now(timezone.utc) - timedelta(hours=1)
lat, lon = 7.4443, 3.9000
for i in range(40):                       # driving north-east across campus
    lat += 0.0008
    lon += 0.0006
    speed = 95 if i == 20 else 35         # one over-speeding ping
    if i >= 32:                           # last few pings drift outside the 3 km zone
        lat += 0.004
    send(round(lat, 6), round(lon, 6), speed, t)
    t += timedelta(seconds=30)
for i in range(14):                       # parked: 7 minutes of zero speed closes the trip
    send(round(lat, 6), round(lon, 6), 0, t)
    t += timedelta(seconds=30)
print("Simulation finished: 1 trip, 1 over-speeding alert and a geofence alert should now exist.")
