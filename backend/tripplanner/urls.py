"""
URL configuration for the tripplanner application.
"""

from django.urls import path
from .views import (
    ExportRawPdfView,
    ExportTripPdfView,
    HealthCheckView,
    PlanTripView,
    TripDetailView,
    TripListView,
)

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("plan-trip/", PlanTripView.as_view(), name="plan-trip"),
    path("trips/", TripListView.as_view(), name="trip-list"),
    path("trips/<int:pk>/", TripDetailView.as_view(), name="trip-detail"),
    path("trips/<int:pk>/pdf/", ExportTripPdfView.as_view(), name="trip-export-pdf"),
    path("export-pdf/", ExportRawPdfView.as_view(), name="raw-export-pdf"),
]
