from django.core.management.base import BaseCommand
from tracker.models import Driver, Geofence, Vehicle


class Command(BaseCommand):
    help = "Create demo vehicle, driver and a campus geofence for testing."

    def handle(self, *args, **opts):
        d, _ = Driver.objects.get_or_create(full_name="Demo Driver", defaults={
            "license_no": "LAG-000001", "department": "Works and Transport", "contact_phone": "08000000000"})
        Vehicle.objects.get_or_create(gps_device_id="SIM-001", defaults={
            "plate_number": "UI-001-AA", "make_model": "Toyota Hiace Bus",
            "department": "Works and Transport", "assigned_driver": d})
        Geofence.objects.get_or_create(name="UI Campus", defaults={
            "center_lat": 7.4443, "center_lon": 3.9000, "radius_km": 3.0, "speed_limit_kmh": 80})
        self.stdout.write(self.style.SUCCESS("Demo data created (device id: SIM-001)."))
