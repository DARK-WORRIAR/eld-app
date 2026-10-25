"""
Unit tests validating Hours-of-Service (HOS) 49 CFR Part 395 simulation logic.
"""

from datetime import datetime
from django.test import SimpleTestCase

from tripplanner.services.constants import (
    DUTY_STATUS_DRIVING,
    DUTY_STATUS_OFF_DUTY,
    DUTY_STATUS_ON_DUTY_NOT_DRIVING,
    HOS_BREAK_DURATION_HOURS,
    HOS_CYCLE_RESTART_HOURS,
    HOS_DAILY_RESET_HOURS,
)
from tripplanner.services.hos import (
    build_daily_logs,
    build_dvir_reports,
    build_stops,
    simulate_trip,
)


class HostSimulationTests(SimpleTestCase):
    """
    Validates adherence to FMCSA 49 CFR Part 395 property-carrying driver regulations.
    """

    def setUp(self):
        self.start_dt = datetime(2026, 10, 20, 6, 0, 0)  # 6:00 AM

    def test_short_trip_under_daily_limits(self):
        """A 300-mile trip taking 6 hours should complete without needing daily resets."""
        timeline = simulate_trip(
            leg1_miles=50.0,
            leg1_hours=1.0,
            leg2_miles=250.0,
            leg2_hours=5.0,
            current_cycle_used_hrs=10.0,
            start_time=self.start_dt,
        )

        labels = [s.label for s in timeline]
        # Should not require 10-hour reset or 34-hour restart
        self.assertNotIn("10-Hour Daily Rest & Off-Duty Reset", labels)
        self.assertNotIn("34-Hour Restart (70-Hour Cycle Limit Reached)", labels)

        # Should include pickup and drop-off on-duty periods
        self.assertTrue(any("Cargo Loading" in l for l in labels))
        self.assertTrue(any("Cargo Unloading" in l for l in labels))

    def test_mandatory_30_minute_break_after_8_hours_driving(self):
        """Driving 9 continuous hours must insert a 30-minute rest break after 8 hours."""
        timeline = simulate_trip(
            leg1_miles=0.0,
            leg1_hours=0.0,
            leg2_miles=450.0,
            leg2_hours=9.0,
            current_cycle_used_hrs=0.0,
            start_time=self.start_dt,
        )

        break_segs = [
            s for s in timeline
            if s.status == DUTY_STATUS_OFF_DUTY and "30-Minute Rest Break" in s.label
        ]
        self.assertEqual(len(break_segs), 1)
        self.assertAlmostEqual(break_segs[0].hours, HOS_BREAK_DURATION_HOURS)

    def test_11_hour_driving_limit_triggers_10_hour_reset(self):
        """Driving 16 hours must trigger a 10-hour off-duty reset when 11 driving hours are reached."""
        timeline = simulate_trip(
            leg1_miles=0.0,
            leg1_hours=0.0,
            leg2_miles=800.0,
            leg2_hours=16.0,
            current_cycle_used_hrs=0.0,
            start_time=self.start_dt,
        )

        resets = [
            s for s in timeline
            if s.status == DUTY_STATUS_OFF_DUTY and "10-Hour Daily Rest" in s.label
        ]
        self.assertGreaterEqual(len(resets), 1)
        self.assertAlmostEqual(resets[0].hours, HOS_DAILY_RESET_HOURS)

    def test_70_hour_cycle_limit_triggers_34_hour_restart(self):
        """When starting with 65 hours used and driving 10 hours, a 34-hour restart must trigger."""
        timeline = simulate_trip(
            leg1_miles=50.0,
            leg1_hours=1.0,
            leg2_miles=450.0,
            leg2_hours=9.0,
            current_cycle_used_hrs=66.0,
            start_time=self.start_dt,
        )

        restarts = [
            s for s in timeline
            if "34-Hour Restart" in s.label
        ]
        self.assertGreaterEqual(len(restarts), 1)
        self.assertAlmostEqual(restarts[0].hours, HOS_CYCLE_RESTART_HOURS)

    def test_fueling_interval_every_1000_miles(self):
        """A 2,500-mile cross-country haul must schedule fuel stops at 1,000 and 2,000 miles."""
        timeline = simulate_trip(
            leg1_miles=100.0,
            leg1_hours=2.0,
            leg2_miles=2400.0,
            leg2_hours=48.0,
            current_cycle_used_hrs=0.0,
            start_time=self.start_dt,
        )

        fuel_stops = [s for s in timeline if "Fuel & Walk-Around" in s.label]
        # At 2,500 total miles, 1,000 and 2,000 mile boundaries must trigger fuel stops
        self.assertGreaterEqual(len(fuel_stops), 2)

    def test_daily_logs_integrity_exactly_24_hours_per_day(self):
        """Every single day sheet in build_daily_logs must sum to exactly 24.0 hours."""
        timeline = simulate_trip(
            leg1_miles=120.0,
            leg1_hours=2.5,
            leg2_miles=1400.0,
            leg2_hours=28.0,
            current_cycle_used_hrs=15.0,
            start_time=self.start_dt,
        )

        daily_logs = build_daily_logs(timeline)
        self.assertGreater(len(daily_logs), 1)

        for day in daily_logs:
            totals = day["totals"]
            day_sum = (
                totals[DUTY_STATUS_OFF_DUTY]
                + totals["sleeper"]
                + totals[DUTY_STATUS_DRIVING]
                + totals[DUTY_STATUS_ON_DUTY_NOT_DRIVING]
            )
            self.assertAlmostEqual(
                day_sum,
                24.0,
                places=1,
                msg=f"Day {day['day_number']} totals do not sum to 24.0 hours: {totals}",
            )

    def test_build_stops_returns_formatted_events(self):
        """Stops list must accurately extract non-driving events with citations and timing."""
        timeline = simulate_trip(
            leg1_miles=50.0,
            leg1_hours=1.0,
            leg2_miles=200.0,
            leg2_hours=4.0,
            current_cycle_used_hrs=0.0,
            start_time=self.start_dt,
        )

        stops = build_stops(timeline)
        self.assertGreaterEqual(len(stops), 2)
        pickup_stop = next(s for s in stops if s["type"] == "pickup")
        dropoff_stop = next(s for s in stops if s["type"] == "dropoff")

        self.assertEqual(pickup_stop["duration_hours"], 1.0)
        self.assertEqual(dropoff_stop["duration_hours"], 1.0)

    def test_adverse_driving_conditions_allows_up_to_13_hours_driving(self):
        """Under 49 CFR 395.1(b)(1), driving 12 hours does not trigger a 10-hour rest reset."""
        timeline = simulate_trip(
            leg1_miles=0.0,
            leg1_hours=0.0,
            leg2_miles=600.0,
            leg2_hours=12.0,
            current_cycle_used_hrs=0.0,
            start_time=self.start_dt,
            adverse_conditions_claimed=True,
            adverse_conditions_reason="Severe unexpected blizzard on I-80",
        )

        resets = [
            s for s in timeline
            if s.status == DUTY_STATUS_OFF_DUTY and "10-Hour Daily Rest" in s.label
        ]
        # Under normal 11h rule, 12h driving would trigger a 10h reset.
        # Under adverse conditions (13h limit), it does not trigger a reset.
        self.assertEqual(len(resets), 0)

    def test_adverse_driving_conditions_triggers_reset_at_13_hours(self):
        """Under 49 CFR 395.1(b)(1), exceeding 13 driving hours triggers a mandatory 10-hour reset."""
        timeline = simulate_trip(
            leg1_miles=0.0,
            leg1_hours=0.0,
            leg2_miles=750.0,
            leg2_hours=15.0,
            current_cycle_used_hrs=0.0,
            start_time=self.start_dt,
            adverse_conditions_claimed=True,
            adverse_conditions_reason="Unexpected multi-vehicle interstate pileup",
        )

        resets = [
            s for s in timeline
            if s.status == DUTY_STATUS_OFF_DUTY and "10-Hour Daily Rest" in s.label
        ]
        self.assertGreaterEqual(len(resets), 1)

    def test_adverse_conditions_daily_logs_include_citation_and_audit_flag(self):
        """Daily log sheets must carry adverse condition audit flags and regulatory citations."""
        timeline = simulate_trip(
            leg1_miles=0.0,
            leg1_hours=0.0,
            leg2_miles=600.0,
            leg2_hours=12.0,
            current_cycle_used_hrs=0.0,
            start_time=self.start_dt,
            adverse_conditions_claimed=True,
            adverse_conditions_reason="Flash flooding closure on US-59",
        )

        daily_logs = build_daily_logs(
            timeline,
            adverse_conditions_claimed=True,
            adverse_conditions_reason="Flash flooding closure on US-59",
        )

        self.assertTrue(daily_logs[0]["adverse_conditions_claimed"])
        self.assertEqual(daily_logs[0]["adverse_conditions_reason"], "Flash flooding closure on US-59")
        # Check that citation appears in remarks or segments
        citations = [seg.get("citation", "") for seg in daily_logs[0]["segments"]]
        self.assertTrue(any("395.1(b)(1)" in c for c in citations))

    def test_pre_trip_and_post_trip_dvir_scheduled(self):
        """Dispatches must schedule pre-trip (396.13) and post-trip (396.11) vehicle inspections."""
        timeline = simulate_trip(
            leg1_miles=100.0,
            leg1_hours=2.0,
            leg2_miles=200.0,
            leg2_hours=4.0,
            current_cycle_used_hrs=10.0,
            start_time=self.start_dt,
        )

        labels = [s.label for s in timeline]
        self.assertIn("Pre-Trip Vehicle Inspection (DVIR)", labels)
        self.assertIn("Post-Trip Vehicle Inspection (DVIR)", labels)

        pre_trip = next(s for s in timeline if "Pre-Trip" in s.label)
        post_trip = next(s for s in timeline if "Post-Trip" in s.label)

        self.assertEqual(pre_trip.status, DUTY_STATUS_ON_DUTY_NOT_DRIVING)
        self.assertEqual(post_trip.status, DUTY_STATUS_ON_DUTY_NOT_DRIVING)
        self.assertIn("396.13", pre_trip.citation)
        self.assertIn("396.11", post_trip.citation)

    def test_build_dvir_reports_structure(self):
        """DVIR generator must construct 12-item FMCSA compliant inspection checklists."""
        timeline = simulate_trip(
            leg1_miles=50.0,
            leg1_hours=1.0,
            leg2_miles=150.0,
            leg2_hours=3.0,
            current_cycle_used_hrs=5.0,
            start_time=self.start_dt,
        )

        reports = build_dvir_reports(timeline)
        self.assertGreaterEqual(len(reports), 2)  # At least Pre-trip + Post-trip

        pre_rep = reports[0]
        self.assertEqual(pre_rep["inspection_type"], "Pre-Trip Inspection")
        self.assertTrue(pre_rep["safe_to_operate"])
        self.assertEqual(pre_rep["overall_condition"], "SATISFACTORY")
        self.assertEqual(len(pre_rep["components"]), 12)
        self.assertIn("service_brakes", [c["id"] for c in pre_rep["components"]])
        self.assertIn("Digitally Signed", pre_rep["driver_certification"]["signature_status"])

    def test_dvir_stops_categorized(self):
        """Inspection stops must be categorized cleanly for timeline and map visualization."""
        timeline = simulate_trip(
            leg1_miles=50.0,
            leg1_hours=1.0,
            leg2_miles=150.0,
            leg2_hours=3.0,
            current_cycle_used_hrs=5.0,
            start_time=self.start_dt,
        )

        stops = build_stops(timeline)
        types = [s["type"] for s in stops]
        self.assertIn("pre_trip_inspection", types)
        self.assertIn("post_trip_inspection", types)



