from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("report/", views.report, name="report"),
    path("api/telemetry", views.api_telemetry, name="api_telemetry"),
    path("api/vehicles/", views.api_vehicles, name="api_vehicles"),
]
