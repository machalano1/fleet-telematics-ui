from django.contrib import admin
from .models import Alert, Driver, Geofence, LocationRecord, Trip, Vehicle

for m in (Alert, Driver, Geofence, LocationRecord, Trip, Vehicle):
    admin.site.register(m)
