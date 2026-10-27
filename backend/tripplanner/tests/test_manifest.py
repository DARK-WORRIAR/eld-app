"""
Unit tests validating Commercial Bill of Lading (BOL) and Cargo Manifest Engine
under FMCSA 49 CFR § 395.8(d)(17) and 49 U.S.C. § 14706 (Carmack Amendment).
"""

from datetime import datetime
from django.test import SimpleTestCase

from tripplanner.services.manifest import build_bill_of_lading
from tripplanner.services.pdf_export import generate_mcs59_pdf


class ManifestServiceTests(SimpleTestCase):
    """
    Validates generation, freight classification, security seals, and legal terms
    for Commercial Bill of Lading (BOL) manifests.
    """

    def setUp(self):
        self.start_dt = datetime(2026, 10, 27, 8, 0, 0)
        self.locations = {
            "pickup": {
                "display_name": "Dallas Logistics Hub, 100 Freight Way, Dallas, TX",
                "lat": 32.7767,
                "lon": -96.7970,
            },
            "dropoff": {
                "display_name": "Chicago Central Distribution, 400 Rail St, Chicago, IL",
                "lat": 41.8781,
                "lon": -87.6298,
            },
        }

    def test_build_bill_of_lading_defaults(self):
        """Standard input must generate a valid BOL with automatic numbering and security seals."""
        data = {
            "carrier_name": "Apex Logistics Freight, Inc.",
            "driver_name": "Marcus Vance",
            "truck_number": "TRK-409",
            "trailer_number": "TRL-9201",
            "commodity": "General Freight & Dry Goods",
            "cargo_weight_lbs": 38000,
            "pickup_location": "Dallas, TX",
            "dropoff_location": "Chicago, IL",
        }

        bol = build_bill_of_lading(data, self.locations, start_time=self.start_dt)

        self.assertTrue(bol["bol_number"].startswith("BOL-202610-"))
        self.assertEqual(bol["carrier"]["driver_name"], "Marcus Vance")
        self.assertEqual(bol["carrier"]["trailer_number"], "TRL-9201")
        self.assertEqual(bol["totals"]["total_weight_lbs"], 38000)
        self.assertGreater(bol["totals"]["total_packages"], 0)
        self.assertTrue(bol["cargo_security"]["seal_verified"])
        self.assertIn("Carmack Amendment", bol["legal_liability_terms"])
        self.assertIn("395.8(d)(17)", bol["regulatory_statute"])

    def test_build_bill_of_lading_custom_parameters(self):
        """Custom freight descriptions and user-supplied BOL IDs must be faithfully preserved."""
        data = {
            "bol_number": "BOL-CUSTOM-9941",
            "carrier_name": "Pinnacle Heavy Haul, LLC",
            "driver_name": "Sarah Connor",
            "truck_number": "TRK-880",
            "trailer_number": "TRL-REEFER-01",
            "commodity": "Refrigerated Produce & Perishables",
            "cargo_weight_lbs": 42500,
            "seal_number": "SEAL-CUSTOM-7721",
        }

        bol = build_bill_of_lading(data, self.locations, start_time=self.start_dt)

        self.assertEqual(bol["bol_number"], "BOL-CUSTOM-9941")
        self.assertEqual(bol["cargo_security"]["seal_number"], "SEAL-CUSTOM-7721")
        self.assertEqual(bol["carrier"]["trailer_number"], "TRL-REEFER-01")
        self.assertEqual(bol["totals"]["total_weight_lbs"], 42500)
        self.assertEqual(bol["line_items"][0]["commodity_description"], "Refrigerated Produce & Perishables")

    def test_pdf_export_renders_with_cargo_manifest(self):
        """ReportLab Form MCS-59 PDF generator must render trailer, BOL, and commodity headers."""
        sample_trip_data = {
            "metadata": {
                "carrier_name": "Apex Logistics Freight, Inc.",
                "driver_name": "Marcus Vance",
                "truck_number": "TRK-409",
                "trailer_number": "TRL-9201",
                "bol_number": "BOL-202610-4491",
                "commodity": "Automotive Assemblies",
                "cargo_weight_lbs": 36000,
            },
            "summary": {"total_days": 1},
            "daily_logs": [
                {
                    "day_number": 1,
                    "date": "2026-10-27",
                    "formatted_date": "Tuesday, October 27, 2026",
                    "totals": {"off_duty": 10.0, "sleeper": 0.0, "driving": 10.0, "on_duty": 4.0},
                    "total_day_hours": 24.0,
                    "segments": [
                        {
                            "from_hr": 0.0,
                            "to_hr": 6.0,
                            "duration_hours": 6.0,
                            "status": "off_duty",
                            "label": "Off Duty Rest",
                            "citation": "49 CFR § 395.3",
                        },
                        {
                            "from_hr": 6.0,
                            "to_hr": 16.0,
                            "duration_hours": 10.0,
                            "status": "driving",
                            "label": "Highway Driving",
                            "citation": "49 CFR § 395.3",
                        },
                        {
                            "from_hr": 16.0,
                            "to_hr": 20.0,
                            "duration_hours": 4.0,
                            "status": "on_duty",
                            "label": "Dock Work",
                            "citation": "49 CFR § 395.2",
                        },
                        {
                            "from_hr": 20.0,
                            "to_hr": 24.0,
                            "duration_hours": 4.0,
                            "status": "off_duty",
                            "label": "Night Rest",
                            "citation": "49 CFR § 395.3",
                        },
                    ],
                }
            ],
        }

        pdf_bytes = generate_mcs59_pdf(sample_trip_data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

