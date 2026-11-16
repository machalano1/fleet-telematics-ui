"""Models mirror the tables in Chapter 3 (Tables 3.1 - 3.6).
The User table is handled by Django's built-in auth User (passwords are stored hashed)."""
from django.db import models


class Driver(models.Model):
    full_name = models.CharField(max_length=100)
    license_no = models.CharField(max_length=30)
    department = models.CharField(max_length=60, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.full_name


class Vehicle(models.Model):
    STATUS = [("Available", "Available"), ("In-Use", "In-Use"), ("Maintenance", "Maintenance")]
    plate_number = models.CharField(max_length=20, unique=True)
    make_model = models.CharField(max_length=50, blank=True)
    gps_device_id = models.CharField(max_length=30, unique=True)
    department = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="Available")
    assigned_driver = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.plate_number


class Trip(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="trips")
    driver = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL, related_name="trips")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    last_moving_at = models.DateTimeField(null=True, blank=True)
    distance_covered = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # km
    average_speed = models.DecimalField(max_digits=6, decimal_places=2, default=0)     # km/h

    def __str__(self):
        return f"Trip {self.pk} - {self.vehicle}"


class LocationRecord(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="locations")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    speed = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    timestamp = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["vehicle", "timestamp"])]


class Alert(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="alerts")
    alert_type = models.CharField(max_length=30)  # "Geofence Breach" / "Over-Speeding"
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField()

    class Meta:
        ordering = ["-timestamp"]


class Geofence(models.Model):
    """Approved zone: a circle (centre + radius). Fleet Managers create these in the admin."""
    name = models.CharField(max_length=60)
    center_lat = models.FloatField()
    center_lon = models.FloatField()
    radius_km = models.FloatField(default=3.0)
    speed_limit_kmh = models.PositiveIntegerField(default=80)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
