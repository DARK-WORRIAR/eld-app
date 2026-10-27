"""
Data validation and serialization schemas for dispatch requests and trip records.
"""

from rest_framework import serializers
from .models import Trip


class TripInputSerializer(serializers.Serializer):
    """
    Validates payload parameters submitted for automated trip dispatch planning.
    """

    current_location = serializers.CharField(
        max_length=255,
        required=True,
        trim_whitespace=True,
        error_messages={
            "blank": "Current location (origin) cannot be blank.",
            "required": "Current location is required.",
        },
    )
    pickup_location = serializers.CharField(
        max_length=255,
        required=True,
        trim_whitespace=True,
        error_messages={
            "blank": "Pickup location cannot be blank.",
            "required": "Pickup location is required.",
        },
    )
    dropoff_location = serializers.CharField(
        max_length=255,
        required=True,
        trim_whitespace=True,
        error_messages={
            "blank": "Drop-off location cannot be blank.",
            "required": "Drop-off location is required.",
        },
    )
    current_cycle_used_hrs = serializers.FloatField(
        min_value=0.0,
        max_value=70.0,
        required=True,
        error_messages={
            "min_value": "Current cycle hours must be at least 0.0.",
            "max_value": "Current cycle hours cannot exceed 70.0 under the 70-hour/8-day rule.",
            "invalid": "Current cycle hours must be a valid number.",
        },
    )
    start_time = serializers.DateTimeField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Optional planned departure datetime (ISO-8601).",
    )
    driver_name = serializers.CharField(
        max_length=120,
        required=False,
        default="Commercial Driver",
        trim_whitespace=True,
    )
    carrier_name = serializers.CharField(
        max_length=150,
        required=False,
        default="Apex Logistics Freight, Inc.",
        trim_whitespace=True,
    )
    truck_number = serializers.CharField(
        max_length=50,
        required=False,
        default="TRK-409",
        trim_whitespace=True,
    )
    trailer_number = serializers.CharField(
        max_length=50,
        required=False,
        default="TRL-9201",
        trim_whitespace=True,
        help_text="Commercial trailer identifier (49 CFR § 395.8(d)(11)).",
    )
    bol_number = serializers.CharField(
        max_length=60,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
        help_text="Shipping document or Bill of Lading number (49 CFR § 395.8(d)(17)).",
    )
    commodity = serializers.CharField(
        max_length=200,
        required=False,
        default="General Freight & Dry Goods",
        trim_whitespace=True,
        help_text="Commodity description / cargo type.",
    )
    cargo_weight_lbs = serializers.IntegerField(
        required=False,
        default=38000,
        min_value=0,
        max_value=80000,
        help_text="Gross cargo weight in pounds (0 to 80,000 lbs).",
    )
    seal_number = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default="SEAL-89104",
        trim_whitespace=True,
        help_text="Security tamper-evident cargo seal number.",
    )
    adverse_conditions_claimed = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Claim 49 CFR § 395.1(b)(1) Adverse Driving Conditions exception (+2 hrs).",
    )
    adverse_conditions_reason = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
        help_text="Documented justification for claiming adverse driving conditions.",
    )

    def validate(self, attrs):
        pickup = attrs.get("pickup_location", "").strip().lower()
        dropoff = attrs.get("dropoff_location", "").strip().lower()

        if pickup and dropoff and pickup == dropoff:
            raise serializers.ValidationError({
                "dropoff_location": "Pickup and drop-off locations cannot be identical."
            })

        return attrs


class TripSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight summary representation for listing historical trips.
    """

    total_distance_miles = serializers.FloatField(read_only=True)
    total_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "driver_name",
            "carrier_name",
            "truck_number",
            "trailer_number",
            "bol_number",
            "commodity",
            "cargo_weight_lbs",
            "seal_number",
            "current_location",
            "pickup_location",
            "dropoff_location",
            "current_cycle_used_hrs",
            "start_time",
            "adverse_conditions_claimed",
            "adverse_conditions_reason",
            "dvir_inspections_logged",
            "total_distance_miles",
            "total_days",
            "created_at",
        ]


class TripDetailSerializer(serializers.ModelSerializer):
    """
    Full detail representation including full route coordinates, stops, and daily log grids.
    """

    class Meta:
        model = Trip
        fields = [
            "id",
            "driver_name",
            "carrier_name",
            "truck_number",
            "trailer_number",
            "bol_number",
            "commodity",
            "cargo_weight_lbs",
            "seal_number",
            "current_location",
            "pickup_location",
            "dropoff_location",
            "current_cycle_used_hrs",
            "start_time",
            "result_json",
            "created_at",
        ]
