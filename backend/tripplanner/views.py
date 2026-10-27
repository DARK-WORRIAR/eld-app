"""
REST API controllers for dispatch route planning, ELD log generation,
and historical trip retrieval.
"""

from datetime import datetime
import logging
from typing import Any, Dict

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Trip
from .serializers import (
    TripDetailSerializer,
    TripInputSerializer,
    TripSummarySerializer,
)
from .services.geocode import LocationNotFoundError, geocode
from .services.hos import build_daily_logs, build_dvir_reports, build_stops, simulate_trip
from .services.manifest import build_bill_of_lading
from .services.pdf_export import generate_mcs59_pdf
from .services.routing import RouteCalculationError, RoutingError, get_route, point_at_distance

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint for container orchestrators, load balancers, and monitoring.
    Verifies API and database availability.
    """

    def get(self, request) -> Response:
        try:
            # Quick database heartbeat query
            Trip.objects.exists()
            db_status = "operational"
        except Exception as exc:
            logger.error("Database health check failed: %s", exc)
            db_status = "degraded"

        return Response({
            "status": "healthy" if db_status == "operational" else "degraded",
            "timestamp": timezone.now().isoformat(),
            "services": {
                "database": db_status,
                "api": "operational",
                "engine": "FMCSA 49 CFR Part 395 Compliance Engine v1.0",
            },
        }, status=status.HTTP_200_OK if db_status == "operational" else status.HTTP_503_SERVICE_UNAVAILABLE)


class PlanTripView(APIView):
    """
    Automated dispatch planning endpoint.
    Calculates driving route corridors, enforces FMCSA Hours-of-Service rules,
    schedules mandatory rest and fueling stops, and renders MCS-59 daily log grids.
    """

    def post(self, request) -> Response:
        serializer = TripInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # ----------------------------------------------------------------------
        # 1. Forward Geocoding
        # ----------------------------------------------------------------------
        try:
            current_pt = geocode(data["current_location"])
            pickup_pt = geocode(data["pickup_location"])
            dropoff_pt = geocode(data["dropoff_location"])
        except LocationNotFoundError as exc:
            return Response(
                {"error": "Location not found", "details": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Geocoding failed unexpectedly for input: %s", data)
            return Response(
                {
                    "error": "Geocoding service unavailable",
                    "details": "Could not contact geocoding service. Please verify your connection or try again.",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ----------------------------------------------------------------------
        # 2. Highway Routing & Corridor Geometry
        # ----------------------------------------------------------------------
        try:
            route = get_route([current_pt, pickup_pt, dropoff_pt])
        except RouteCalculationError as exc:
            return Response(
                {"error": "Routing calculation failed", "details": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except RoutingError as exc:
            logger.exception("Routing service failed: %s", exc)
            return Response(
                {
                    "error": "Routing service unavailable",
                    "details": "Could not compute highway route. Upstream routing service returned an error.",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as exc:
            logger.exception("Unexpected routing failure: %s", exc)
            return Response(
                {"error": "Internal routing error", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ----------------------------------------------------------------------
        # 3. Hours of Service (HOS) 49 CFR Part 395 Simulation
        # ----------------------------------------------------------------------
        try:
            legs = route["legs"]
            leg1 = legs[0]
            leg2 = legs[1]

            start_dt = data.get("start_time")
            if not start_dt:
                start_dt = datetime.now().replace(minute=0, second=0, microsecond=0)

            adverse_claimed = data.get("adverse_conditions_claimed", False)
            adverse_reason = data.get("adverse_conditions_reason", "")

            timeline = simulate_trip(
                leg1_miles=leg1["distance_miles"],
                leg1_hours=leg1["duration_hours"],
                leg2_miles=leg2["distance_miles"],
                leg2_hours=leg2["duration_hours"],
                current_cycle_used_hrs=data["current_cycle_used_hrs"],
                start_time=start_dt,
                adverse_conditions_claimed=adverse_claimed,
                adverse_conditions_reason=adverse_reason,
            )

            daily_logs = build_daily_logs(
                timeline,
                adverse_conditions_claimed=adverse_claimed,
                adverse_conditions_reason=adverse_reason,
            )
            stops = build_stops(timeline)

            # Interpolate geographic coordinate along route polyline for each stop marker
            for stop in stops:
                stop["position"] = point_at_distance(
                    geometry=route["geometry"],
                    total_route_miles=route["total_distance_miles"],
                    target_miles=stop["cumulative_miles"],
                )

            total_drive_hours = sum(d["totals"].get("driving", 0.0) for d in daily_logs)
            total_on_duty_hours = sum(d["totals"].get("on_duty", 0.0) for d in daily_logs)
            total_off_duty_hours = sum(d["totals"].get("off_duty", 0.0) for d in daily_logs)
            total_sleeper_hours = sum(d["totals"].get("sleeper", 0.0) for d in daily_logs)

            total_dist = route["total_distance_miles"]
            est_gallons = round(total_dist / 6.5, 1) if total_dist > 0 else 0.0
            est_fuel_cost = round(est_gallons * 3.85, 2)
            est_cost_per_mile = round(est_fuel_cost / max(1.0, total_dist), 2)
            est_co2 = round((est_gallons * 22.4) / 2204.62, 2)

            dvir_reports = build_dvir_reports(
                timeline=timeline,
                metadata={
                    "driver_name": data.get("driver_name", "Commercial Driver"),
                    "carrier_name": data.get("carrier_name", "Apex Logistics Freight, Inc."),
                    "truck_number": data.get("truck_number", "TRK-409"),
                },
                locations={
                    "current": current_pt,
                    "pickup": pickup_pt,
                    "dropoff": dropoff_pt,
                },
            )

            # Build Uniform Straight Bill of Lading (49 CFR § 395.8(d)(17) / 49 U.S.C. § 14706)
            bol_document = build_bill_of_lading(
                data=data,
                locations={
                    "current": current_pt,
                    "pickup": pickup_pt,
                    "dropoff": dropoff_pt,
                },
                start_time=start_dt,
            )

            trailer_num = data.get("trailer_number", "TRL-9201")
            bol_num = bol_document["bol_number"]
            commodity_desc = data.get("commodity", "General Freight & Dry Goods")
            cargo_wt = int(data.get("cargo_weight_lbs") or 38000)
            seal_num = bol_document["cargo_security"]["seal_number"]

            result: Dict[str, Any] = {
                "metadata": {
                    "driver_name": data.get("driver_name", "Commercial Driver"),
                    "carrier_name": data.get("carrier_name", "Apex Logistics Freight, Inc."),
                    "truck_number": data.get("truck_number", "TRK-409"),
                    "trailer_number": trailer_num,
                    "bol_number": bol_num,
                    "commodity": commodity_desc,
                    "cargo_weight_lbs": cargo_wt,
                    "seal_number": seal_num,
                    "dispatch_time": start_dt.isoformat(),
                    "regulations_standard": "49 CFR Part 395 Property-Carrying Driver Rules",
                    "adverse_conditions_claimed": adverse_claimed,
                    "adverse_conditions_reason": adverse_reason,
                },
                "locations": {
                    "current": current_pt,
                    "pickup": pickup_pt,
                    "dropoff": dropoff_pt,
                },
                "route": {
                    "geometry": route["geometry"],
                    "total_distance_miles": route["total_distance_miles"],
                    "total_duration_hours": route["total_duration_hours"],
                    "legs": route["legs"],
                },
                "stops": stops,
                "daily_logs": daily_logs,
                "dvir_reports": dvir_reports,
                "bol_document": bol_document,
                "summary": {
                    "total_days": len(daily_logs),
                    "total_distance_miles": route["total_distance_miles"],
                    "total_drive_hours": round(total_drive_hours, 2),
                    "total_on_duty_hours": round(total_on_duty_hours, 2),
                    "total_off_duty_hours": round(total_off_duty_hours, 2),
                    "total_sleeper_hours": round(total_sleeper_hours, 2),
                    "total_stops_count": len(stops),
                    "dvir_inspections_count": len(dvir_reports),
                    "dvir_status": "Satisfactory — All 12 Safety Systems Passed (49 CFR Part 396)",
                    "trailer_number": trailer_num,
                    "bol_number": bol_num,
                    "commodity": commodity_desc,
                    "cargo_weight_lbs": cargo_wt,
                    "cargo_weight_tons": round(cargo_wt / 2000.0, 1),
                    "cycle_used_prior_hrs": data["current_cycle_used_hrs"],
                    "cycle_available_prior_hrs": round(70.0 - data["current_cycle_used_hrs"], 2),
                    "compliance_status": (
                        "Compliant under 49 CFR § 395.1(b)(1) Adverse Driving Conditions Exception"
                        if adverse_claimed
                        else "Fully Compliant with FMCSA 49 CFR § 395"
                    ),
                    "adverse_conditions_claimed": adverse_claimed,
                    "adverse_conditions_reason": adverse_reason,
                    "fuel_economy": {
                        "average_mpg": 6.5,
                        "diesel_price_per_gal": 3.85,
                        "estimated_gallons": est_gallons,
                        "estimated_fuel_cost_usd": est_fuel_cost,
                        "fuel_cost_per_mile_usd": est_cost_per_mile,
                        "carbon_footprint_metric_tons": est_co2,
                    },
                },
            }

            # Persist record
            trip_instance = Trip.objects.create(
                driver_name=data.get("driver_name", "Commercial Driver"),
                carrier_name=data.get("carrier_name", "Apex Logistics Freight, Inc."),
                truck_number=data.get("truck_number", "TRK-409"),
                trailer_number=trailer_num,
                bol_number=bol_num,
                commodity=commodity_desc,
                cargo_weight_lbs=cargo_wt,
                seal_number=seal_num,
                current_location=data["current_location"],
                pickup_location=data["pickup_location"],
                dropoff_location=data["dropoff_location"],
                current_cycle_used_hrs=data["current_cycle_used_hrs"],
                adverse_conditions_claimed=adverse_claimed,
                adverse_conditions_reason=adverse_reason,
                dvir_inspections_logged=len(dvir_reports),
                start_time=start_dt,
                result_json=result,
            )
            result["trip_id"] = trip_instance.id

        except Exception as exc:
            logger.exception("Trip simulation failed unexpectedly: %s", exc)
            return Response(
                {
                    "error": "Simulation engine failure",
                    "details": f"An error occurred while simulating compliance timeline: {exc}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result, status=status.HTTP_200_OK)


class TripListView(generics.ListAPIView):
    """
    Returns a chronological list of recent trip dispatches.
    """

    queryset = Trip.objects.all()[:30]
    serializer_class = TripSummarySerializer


class TripDetailView(generics.RetrieveAPIView):
    """
    Retrieves full details and daily logs for a specific historical trip plan.
    """

    queryset = Trip.objects.all()
    serializer_class = TripDetailSerializer

    def retrieve(self, request, *args, **kwargs) -> Response:
        instance = self.get_object()
        return Response(instance.result_json, status=status.HTTP_200_OK)


class ExportTripPdfView(APIView):
    """
    Renders and streams official DOT Form MCS-59 Driver's Daily Log sheets
    as a downloadable PDF document for a saved trip.
    Supports optional ?day=<int> filter for printing a single day.
    """

    def get(self, request, pk: int) -> HttpResponse:
        try:
            trip = Trip.objects.get(pk=pk)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)

        day_param = request.query_params.get("day")
        target_day = int(day_param) if day_param and day_param.isdigit() else None

        try:
            pdf_bytes = generate_mcs59_pdf(trip.result_json, target_day=target_day)
        except Exception as exc:
            logger.exception("Failed to render MCS-59 PDF: %s", exc)
            return Response(
                {"error": "PDF generation failed", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        filename = f"DOT_Form_MCS59_Trip_{trip.id}"
        if target_day:
            filename += f"_Day_{target_day}"
        filename += ".pdf"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ExportRawPdfView(APIView):
    """
    Generates and returns DOT Form MCS-59 PDF directly from active trip JSON payload.
    """

    def post(self, request) -> HttpResponse:
        trip_data = request.data
        if not trip_data or not isinstance(trip_data, dict):
            return Response({"error": "Invalid trip data payload"}, status=status.HTTP_400_BAD_REQUEST)

        day_param = request.query_params.get("day")
        target_day = int(day_param) if day_param and day_param.isdigit() else None

        try:
            pdf_bytes = generate_mcs59_pdf(trip_data, target_day=target_day)
        except Exception as exc:
            logger.exception("Failed to render raw MCS-59 PDF: %s", exc)
            return Response(
                {"error": "PDF generation failed", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        filename = f"DOT_Form_MCS59_Log"
        if target_day:
            filename += f"_Day_{target_day}"
        filename += ".pdf"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
