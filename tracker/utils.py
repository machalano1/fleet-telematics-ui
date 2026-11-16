"""Pure helper functions (no Django imports) so they are easy to unit-test."""
import math


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two GPS points, in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def inside_circle(lat, lon, c_lat, c_lon, radius_km):
    return haversine_km(lat, lon, c_lat, c_lon) <= radius_km


def utilization_pct(active_hours, total_hours):
    """Appendix B: utilization = active hours / total clock hours * 100."""
    return 0.0 if total_hours <= 0 else (active_hours / total_hours) * 100


def utilization_flag(pct, low=30, high=80):
    if pct < low:
        return "Underutilized"
    if pct > high:
        return "Critical Capacity"
    return "Normal"
