"""
Data models for persisting trip plans, dispatch parameters, and ELD compliance records.
"""

from django.db import models


class Trip(models.Model):
    """
    Persisted record of an ELD-compliant commercial freight trip plan.
    Stores route waypoints, driver cycle metrics, and calculated compliance timeline.
    """

    driver_name = models.CharField(
        max_length=120,
        default="Commercial Driver",
        help_text="Name of the primary property-carrying driver.",
    )
    carrier_name = models.CharField(
        max_length=150,
        default="Apex Logistics Freight, Inc.",
        help_text="Authorized motor carrier name.",
    )
    truck_number = models.CharField(
        max_length=50,
        default="TRK-409",
        help_text="Commercial vehicle / tractor identification number.",
    )

    current_location = models.CharField(
        max_length=255,
        help_text="Dispatch origin or current tractor location.",
    )
    pickup_location = models.CharField(
        max_length=255,
        help_text="Shipper facility origin location.",
    )
    dropoff_location = models.CharField(
        max_length=255,
        help_text="Receiver destination location.",
    )

    current_cycle_used_hrs = models.FloatField(
        help_text="Driver's cumulative on-duty hours logged prior to dispatch (0.0 to 70.0).",
    )
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled departure date and time.",
    )
    adverse_conditions_claimed = models.BooleanField(
        default=False,
        help_text="Whether 49 CFR § 395.1(b)(1) Adverse Driving Conditions exception was claimed.",
    )
    adverse_conditions_reason = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Documented justification for claiming the adverse driving exception.",
    )

    result_json = models.JSONField(
        help_text="Complete JSON payload containing routes, stops, and daily log grids.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when the trip plan was generated.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Trip Plan"
        verbose_name_plural = "Trip Plans"

    def __str__(self) -> str:
        return f"{self.pickup_location} -> {self.dropoff_location} ({self.created_at:%Y-%m-%d %H:%M})"

    @property
    def total_distance_miles(self) -> float:
        """Returns total calculated distance in miles from the result payload."""
        if isinstance(self.result_json, dict):
            return self.result_json.get("route", {}).get("total_distance_miles", 0.0)
        return 0.0

    @property
    def total_days(self) -> int:
        """Returns total number of calendar days spanned by this trip."""
        if isinstance(self.result_json, dict):
            return self.result_json.get("summary", {}).get("total_days", 1)
        return 1
