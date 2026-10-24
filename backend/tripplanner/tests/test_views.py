"""
Integration tests for API views and serialization validation.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from tripplanner.models import Trip


class TripApiTests(TestCase):
    """
    Validates REST API endpoints and input validation schemas.
    """

    def setUp(self):
        self.client = APIClient()

    def test_health_check_endpoint(self):
        """GET /api/health/ should return 200 OK with operational status."""
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")
        self.assertIn("services", response.data)

    def test_trip_input_validation_empty_payload(self):
        """Empty payload should return 400 Bad Request with field errors."""
        response = self.client.post("/api/plan-trip/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("details", response.data)

    def test_trip_input_validation_cycle_hours_exceeded(self):
        """Current cycle hours > 70 should return 400 Bad Request."""
        payload = {
            "current_location": "Dallas, TX",
            "pickup_location": "Oklahoma City, OK",
            "dropoff_location": "Chicago, IL",
            "current_cycle_used_hrs": 75.0,  # Invalid: > 70
        }
        response = self.client.post("/api/plan-trip/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_trip_input_validation_identical_locations(self):
        """Pickup and dropoff being identical should fail validation."""
        payload = {
            "current_location": "Dallas, TX",
            "pickup_location": "Chicago, IL",
            "dropoff_location": "Chicago, IL",
            "current_cycle_used_hrs": 12.0,
        }
        response = self.client.post("/api/plan-trip/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_trip_list_endpoint(self):
        """GET /api/trips/ returns list of historical trips."""
        Trip.objects.create(
            current_location="Dallas, TX",
            pickup_location="Oklahoma City, OK",
            dropoff_location="Chicago, IL",
            current_cycle_used_hrs=10.0,
            result_json={"summary": {"total_days": 2}},
        )

        response = self.client.get("/api/trips/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pickup_location"], "Oklahoma City, OK")

