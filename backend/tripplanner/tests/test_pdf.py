"""
Unit tests validating ReportLab Form MCS-59 PDF document generation and API endpoints.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from tripplanner.models import Trip
from tripplanner.services.pdf_export import generate_mcs59_pdf


class PdfExportTests(TestCase):
    """
    Validates binary PDF construction and HTTP PDF stream delivery.
    """

    def setUp(self):
        self.client = APIClient()
        self.sample_trip_payload = {
            "metadata": {
                "driver_name": "Marcus Vance",
                "carrier_name": "Apex Logistics Freight, Inc.",
                "truck_number": "TRK-840",
            },
            "summary": {"total_days": 1},
            "daily_logs": [
                {
                    "day_number": 1,
                    "date": "2026-10-24",
                    "formatted_date": "Saturday, October 24, 2026",
                    "totals": {
                        "off_duty": 13.0,
                        "sleeper": 0.0,
                        "driving": 10.0,
                        "on_duty": 1.0,
                    },
                    "segments": [
                        {
                            "status": "off_duty",
                            "from_hr": 0.0,
                            "to_hr": 6.0,
                            "duration_hours": 6.0,
                            "label": "Off-Duty Rest",
                        },
                        {
                            "status": "on_duty",
                            "from_hr": 6.0,
                            "to_hr": 7.0,
                            "duration_hours": 1.0,
                            "label": "Cargo Loading",
                        },
                        {
                            "status": "driving",
                            "from_hr": 7.0,
                            "to_hr": 17.0,
                            "duration_hours": 10.0,
                            "label": "En Route",
                        },
                        {
                            "status": "off_duty",
                            "from_hr": 17.0,
                            "to_hr": 24.0,
                            "duration_hours": 7.0,
                            "label": "Post-Delivery Off-Duty",
                        },
                    ],
                }
            ],
        }

    def test_generate_mcs59_pdf_returns_valid_pdf_binary(self):
        """Service function must return bytes starting with standard PDF header '%PDF-'."""
        pdf_bytes = generate_mcs59_pdf(self.sample_trip_payload)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_export_raw_pdf_endpoint(self):
        """POST /api/export-pdf/ with trip JSON should return 200 with application/pdf."""
        response = self.client.post(
            "/api/export-pdf/",
            data=self.sample_trip_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment; filename=", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))

    def test_export_trip_pdf_by_id_endpoint(self):
        """GET /api/trips/<pk>/pdf/ should stream PDF for a saved database record."""
        trip = Trip.objects.create(
            current_location="Dallas, TX",
            pickup_location="Oklahoma City, OK",
            dropoff_location="Chicago, IL",
            current_cycle_used_hrs=10.0,
            result_json=self.sample_trip_payload,
        )

        response = self.client.get(f"/api/trips/{trip.id}/pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))

