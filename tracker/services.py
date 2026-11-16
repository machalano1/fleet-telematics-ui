"""Core telematics logic: store a GPS ping, open/close trips, raise alerts."""
from datetime import timedelta
from decimal import Decimal

from django.conf import settings

from .models import Alert, Geofence, LocationRecord, Trip
from .utils import haversine_km, inside_circle


def _recent_alert_exists(vehicle, alert_type, ts, minutes=5):
    return Alert.objects.filter(
        vehicle=vehicle, alert_type=alert_type, timestamp__gte=ts - timedelta(minutes=minutes)
    ).exists()


def _raise(vehicle, alert_type, message, ts):
    if not _recent_alert_exists(vehicle, alert_type, ts):
        Alert.objects.create(vehicle=vehicle, alert_type=alert_type, message=message, timestamp=ts)


def process_ping(vehicle, lat, lon, speed, ts):
    prev = (LocationRecord.objects.filter(vehicle=vehicle, timestamp__lt=ts)
            .order_by("-timestamp").first())
    LocationRecord.objects.create(vehicle=vehicle, latitude=lat, longitude=lon, speed=speed, timestamp=ts)

    moving = speed >= settings.MOVING_SPEED_KMH
    trip = Trip.objects.filter(vehicle=vehicle, end_time__isnull=True).order_by("-start_time").first()

    # 1. Open a trip when motion is detected
    if trip is None and moving:
        trip = Trip.objects.create(vehicle=vehicle, driver=vehicle.assigned_driver,
                                   start_time=ts, last_moving_at=ts)
        vehicle.status = "In-Use"
        vehicle.save(update_fields=["status"])

    # 2. Update or close the open trip
    if trip is not None:
        if moving:
            if prev is not None:
                d = haversine_km(float(prev.latitude), float(prev.longitude), lat, lon)
                trip.distance_covered = trip.distance_covered + Decimal(str(round(d, 3)))
            trip.last_moving_at = ts
        elif trip.last_moving_at and ts - trip.last_moving_at >= timedelta(minutes=settings.IDLE_MINUTES_TO_CLOSE):
            trip.end_time = trip.last_moving_at   # trip ended when it last moved
            hours = (trip.end_time - trip.start_time).total_seconds() / 3600
            if hours > 0:
                trip.average_speed = Decimal(str(round(float(trip.distance_covered) / hours, 2)))
            vehicle.status = "Available"
            vehicle.save(update_fields=["status"])
        trip.save()

    # 3. Alerts: over-speeding and geofence breach
    fences = list(Geofence.objects.filter(active=True))
    limit = min([f.speed_limit_kmh for f in fences], default=settings.DEFAULT_SPEED_LIMIT_KMH)
    if speed > limit:
        _raise(vehicle, "Over-Speeding", f"{vehicle.plate_number} at {speed:.0f} km/h (limit {limit}).", ts)
    if fences and not any(inside_circle(lat, lon, f.center_lat, f.center_lon, f.radius_km) for f in fences):
        _raise(vehicle, "Geofence Breach", f"{vehicle.plate_number} is outside all approved zones.", ts)
