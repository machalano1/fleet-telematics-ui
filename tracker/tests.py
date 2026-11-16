from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from .models import Alert, Geofence, Trip, Vehicle
from .services import process_ping
from .utils import haversine_km, utilization_flag, utilization_pct


class UtilsTests(TestCase):
    def test_haversine_zero(self):
        self.assertAlmostEqual(haversine_km(7.44, 3.9, 7.44, 3.9), 0, places=6)

    def test_haversine_one_degree_latitude(self):
        self.assertAlmostEqual(haversine_km(0, 0, 1, 0), 111.19, delta=0.2)

    def test_utilization_flags(self):
        self.assertEqual(utilization_flag(utilization_pct(2, 24)), "Underutilized")
        self.assertEqual(utilization_flag(utilization_pct(12, 24)), "Normal")
        self.assertEqual(utilization_flag(utilization_pct(21, 24)), "Critical Capacity")


class TripTests(TestCase):
    def setUp(self):
        self.v = Vehicle.objects.create(plate_number="T-1", gps_device_id="D1")
        Geofence.objects.create(name="Z", center_lat=7.4443, center_lon=3.9, radius_km=3, speed_limit_kmh=80)

    def test_trip_opens_and_closes(self):
        t = timezone.now() - timedelta(hours=1)
        lat = 7.4443
        for _ in range(5):
            lat += 0.001
            process_ping(self.v, lat, 3.9, 30, t)
            t += timedelta(seconds=30)
        self.assertEqual(Trip.objects.filter(end_time__isnull=True).count(), 1)
        for _ in range(14):
            process_ping(self.v, lat, 3.9, 0, t)
            t += timedelta(seconds=30)
        trip = Trip.objects.get()
        self.assertIsNotNone(trip.end_time)
        self.assertGreater(trip.distance_covered, 0)

    def test_overspeed_and_geofence_alerts(self):
        t = timezone.now()
        process_ping(self.v, 7.4443, 3.9, 120, t)
        process_ping(self.v, 8.5, 3.9, 30, t + timedelta(minutes=10))
        types = set(Alert.objects.values_list("alert_type", flat=True))
        self.assertEqual(types, {"Over-Speeding", "Geofence Breach"})
