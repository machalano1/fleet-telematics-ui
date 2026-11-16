import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Alert, LocationRecord, Trip, Vehicle
from .services import process_ping
from .utils import utilization_flag, utilization_pct


@csrf_exempt  # the GPS tracker is a device, not a browser, so it cannot send a CSRF token
@require_POST
def api_telemetry(request):
    """POST /api/telemetry  {"device_id": "...", "latitude": 7.44, "longitude": 3.90,
                             "speed": 32.5, "timestamp": "2026-11-16T09:00:00+00:00"}"""
    try:
        data = json.loads(request.body)
        lat, lon = float(data["latitude"]), float(data["longitude"])
        speed = float(data.get("speed", 0))
        device_id = data["device_id"]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "invalid payload"}, status=400)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return JsonResponse({"error": "coordinates out of range"}, status=400)
    try:
        vehicle = Vehicle.objects.get(gps_device_id=device_id)
    except Vehicle.DoesNotExist:
        return JsonResponse({"error": "unknown device"}, status=404)
    ts = parse_datetime(data["timestamp"]) if data.get("timestamp") else timezone.now()
    if ts is None:
        return JsonResponse({"error": "bad timestamp"}, status=400)
    if timezone.is_naive(ts):
        ts = timezone.make_aware(ts)
    process_ping(vehicle, lat, lon, speed, ts)
    return JsonResponse({"status": "ok"})


@login_required
def api_vehicles(request):
    out = []
    for v in Vehicle.objects.all():
        last = v.locations.order_by("-timestamp").first()
        if last:
            out.append({"plate": v.plate_number, "status": v.status, "lat": float(last.latitude),
                        "lon": float(last.longitude), "speed": float(last.speed),
                        "time": last.timestamp.isoformat()})
    return JsonResponse({"vehicles": out})


@login_required
def dashboard(request):
    return render(request, "tracker/dashboard.html", {
        "vehicles": Vehicle.objects.all(),
        "alerts": Alert.objects.select_related("vehicle")[:10],
    })


@login_required
def report(request):
    """Utilization report for the whole fleet or one vehicle over the last N days."""
    try:
        days = max(1, int(request.GET.get("days", 1)))
    except ValueError:
        days = 1
    vehicle_id = request.GET.get("vehicle")
    end = timezone.now()
    start = end - timedelta(days=days)
    total_hours = days * 24.0

    vehicles = Vehicle.objects.all()
    if vehicle_id:
        vehicles = vehicles.filter(pk=vehicle_id)

    rows = []
    for v in vehicles:
        trips = Trip.objects.filter(vehicle=v, start_time__gte=start, end_time__isnull=False)
        active = sum((t.end_time - t.start_time).total_seconds() / 3600 for t in trips)
        km = sum(float(t.distance_covered) for t in trips)
        pct = utilization_pct(active, total_hours)
        rows.append({
            "vehicle": v, "trips": trips.count(), "km": round(km, 2),
            "active": round(active, 2), "idle": round(max(total_hours - active, 0), 2),
            "pct": round(pct, 1),
            "flag": utilization_flag(pct, settings.UNDERUTILIZED_BELOW, settings.CRITICAL_ABOVE),
        })
    return render(request, "tracker/report.html", {
        "rows": rows, "days": days, "start": start, "end": end,
        "all_vehicles": Vehicle.objects.all(), "selected": vehicle_id,
    })
