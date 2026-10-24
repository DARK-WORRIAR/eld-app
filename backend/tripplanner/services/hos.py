"""
Hours-of-Service (HOS) simulation engine modeling FMCSA regulations under 49 CFR Part 395
for property-carrying commercial motor vehicles operating under the 70-hour/8-day rule.

Regulatory Framework Modeled:
  - 11-Hour Driving Limit: 49 CFR § 395.3(a)(3)(i)
  - 14-Hour Duty Window: 49 CFR § 395.3(a)(2)
  - 30-Minute Rest Break: 49 CFR § 395.3(a)(3)(ii)
  - 10-Hour Daily Reset: 49 CFR § 395.3(a)(1)
  - 70-Hour / 8-Day Cycle Limit: 49 CFR § 395.3(b)(2)
  - 34-Hour Restart: 49 CFR § 395.3(d)
  - Fueling & Inspection Intervals: Fleet standard (every 1,000 miles)
  - Loading / Unloading Terminal Allotments: Fleet standard (1.0 hour each)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
from typing import Any, Dict, List, Optional, Tuple

from .constants import (
    DEFAULT_DROPOFF_HOURS,
    DEFAULT_FUEL_INTERVAL_MILES,
    DEFAULT_FUEL_STOP_HOURS,
    DEFAULT_PICKUP_HOURS,
    DUTY_STATUS_DRIVING,
    DUTY_STATUS_OFF_DUTY,
    DUTY_STATUS_ON_DUTY_NOT_DRIVING,
    HOS_BREAK_DURATION_HOURS,
    HOS_BREAK_THRESHOLD_HOURS,
    HOS_CYCLE_LIMIT_HOURS,
    HOS_CYCLE_RESTART_HOURS,
    HOS_DAILY_RESET_HOURS,
    HOS_DUTY_WINDOW_HOURS,
    HOS_MAX_DRIVING_HOURS,
)

EPSILON = 1e-6


@dataclass
class Segment:
    """Represents a continuous duty status interval during the trip."""
    status: str
    label: str
    start: datetime
    end: datetime
    start_miles: float
    end_miles: float
    citation: Optional[str] = None

    @property
    def hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0


@dataclass
class SimulatorState:
    """Maintains active clocks, odometer, and event history during simulation."""
    now: datetime
    drive_hours_today: float = 0.0
    duty_window_hours: float = 0.0
    drive_since_break: float = 0.0
    cumulative_cycle_hours: float = 0.0
    cumulative_miles: float = 0.0
    timeline: List[Segment] = field(default_factory=list)

    def record_event(
        self,
        status: str,
        label: str,
        duration_hours: float,
        citation: Optional[str] = None,
    ) -> None:
        """Appends a new duty segment to the timeline and advances simulation time."""
        start = self.now
        end = self.now + timedelta(hours=duration_hours)
        miles = self.cumulative_miles
        self.timeline.append(
            Segment(
                status=status,
                label=label,
                start=start,
                end=end,
                start_miles=miles,
                end_miles=miles,
                citation=citation,
            )
        )
        self.now = end


def _partition_leg_by_fuel_stops(
    distance_miles: float,
    duration_hours: float,
    current_odometer: float,
    interval_miles: float = DEFAULT_FUEL_INTERVAL_MILES,
) -> List[Tuple[float, float, bool]]:
    """
    Subdivides a driving leg into sub-legs bounded by 1,000-mile fuel stops.

    Returns:
        List of tuples: (chunk_miles, chunk_hours, requires_fueling)
    """
    if distance_miles <= EPSILON:
        return []

    speed_mph = (distance_miles / duration_hours) if duration_hours > EPSILON else 45.0
    chunks: List[Tuple[float, float, bool]] = []
    miles_remaining = distance_miles
    pos = current_odometer

    while miles_remaining > EPSILON:
        next_boundary = (math.floor(pos / interval_miles) + 1.0) * interval_miles
        miles_to_boundary = next_boundary - pos

        chunk_miles = min(miles_remaining, miles_to_boundary)
        if chunk_miles <= EPSILON:
            chunk_miles = miles_remaining

        chunk_hours = chunk_miles / speed_mph
        is_boundary_hit = (
            abs((pos + chunk_miles) - next_boundary) <= 1e-3
            and (miles_remaining - chunk_miles) > EPSILON
        )

        chunks.append((chunk_miles, chunk_hours, is_boundary_hit))
        pos += chunk_miles
        miles_remaining -= chunk_miles

    return chunks


def _simulate_driving_chunk(
    state: SimulatorState,
    chunk_miles: float,
    chunk_hours: float,
    label: str,
) -> None:
    """
    Simulates driving over a distance chunk, inserting mandatory regulatory breaks,
    daily resets, or 34-hour restarts as FMCSA clocks expire.
    """
    remaining_hours = chunk_hours
    remaining_miles = chunk_miles
    speed_mph = (chunk_miles / chunk_hours) if chunk_hours > EPSILON else 45.0

    while remaining_hours > EPSILON:
        # Evaluate available capacity on all active HOS clocks
        avail_break = max(0.0, HOS_BREAK_THRESHOLD_HOURS - state.drive_since_break)
        avail_drive = max(0.0, HOS_MAX_DRIVING_HOURS - state.drive_hours_today)
        avail_window = max(0.0, HOS_DUTY_WINDOW_HOURS - state.duty_window_hours)
        avail_cycle = max(0.0, HOS_CYCLE_LIMIT_HOURS - state.cumulative_cycle_hours)

        # Drive for whichever limit expires first
        drivable_hours = min(remaining_hours, avail_break, avail_drive, avail_window, avail_cycle)

        if drivable_hours > EPSILON:
            state.record_event(
                status=DUTY_STATUS_DRIVING,
                label=label,
                duration_hours=drivable_hours,
                citation="49 CFR § 395.3",
            )
            dist_covered = drivable_hours * speed_mph
            state.cumulative_miles += dist_covered
            state.timeline[-1].end_miles = state.cumulative_miles

            # Update simulation clocks
            state.drive_hours_today += drivable_hours
            state.duty_window_hours += drivable_hours
            state.drive_since_break += drivable_hours
            state.cumulative_cycle_hours += drivable_hours

            remaining_hours -= drivable_hours
            remaining_miles -= dist_covered
            continue

        # A regulatory clock has expired; resolve according to priority:
        # 1. 30-minute rest break after 8 hours of driving
        if avail_break <= EPSILON:
            state.record_event(
                status=DUTY_STATUS_OFF_DUTY,
                label="Mandatory 30-Minute Rest Break",
                duration_hours=HOS_BREAK_DURATION_HOURS,
                citation="49 CFR § 395.3(a)(3)(ii)",
            )
            state.drive_since_break = 0.0
            # Under FMCSA rules, off-duty rest breaks do NOT pause the 14-hour duty window
            state.duty_window_hours += HOS_BREAK_DURATION_HOURS

        # 2. 10-hour daily reset after 11 driving hours or 14-hour duty window
        elif avail_drive <= EPSILON or avail_window <= EPSILON:
            state.record_event(
                status=DUTY_STATUS_OFF_DUTY,
                label="10-Hour Daily Rest & Off-Duty Reset",
                duration_hours=HOS_DAILY_RESET_HOURS,
                citation="49 CFR § 395.3(a)(1)",
            )
            state.drive_hours_today = 0.0
            state.duty_window_hours = 0.0
            state.drive_since_break = 0.0

        # 3. 34-hour cycle restart after reaching 70 hours in 8 days
        else:
            state.record_event(
                status=DUTY_STATUS_OFF_DUTY,
                label="34-Hour Restart (70-Hour Cycle Limit Reached)",
                duration_hours=HOS_CYCLE_RESTART_HOURS,
                citation="49 CFR § 395.3(d)",
            )
            state.cumulative_cycle_hours = 0.0
            state.drive_hours_today = 0.0
            state.duty_window_hours = 0.0
            state.drive_since_break = 0.0


def _simulate_on_duty_stop(
    state: SimulatorState,
    duration_hours: float,
    label: str,
    citation: Optional[str] = None,
) -> None:
    """
    Simulates a non-driving on-duty activity (loading, unloading, or vehicle inspection).
    Checks if a reset or restart is required before the on-duty task can begin.
    """
    avail_window = max(0.0, HOS_DUTY_WINDOW_HOURS - state.duty_window_hours)
    avail_cycle = max(0.0, HOS_CYCLE_LIMIT_HOURS - state.cumulative_cycle_hours)

    if avail_window <= EPSILON:
        state.record_event(
            status=DUTY_STATUS_OFF_DUTY,
            label="10-Hour Daily Rest & Off-Duty Reset",
            duration_hours=HOS_DAILY_RESET_HOURS,
            citation="49 CFR § 395.3(a)(1)",
        )
        state.drive_hours_today = 0.0
        state.duty_window_hours = 0.0
        state.drive_since_break = 0.0

    if avail_cycle <= EPSILON:
        state.record_event(
            status=DUTY_STATUS_OFF_DUTY,
            label="34-Hour Restart (70-Hour Cycle Limit Reached)",
            duration_hours=HOS_CYCLE_RESTART_HOURS,
            citation="49 CFR § 395.3(d)",
        )
        state.cumulative_cycle_hours = 0.0
        state.drive_hours_today = 0.0
        state.duty_window_hours = 0.0
        state.drive_since_break = 0.0

    state.record_event(
        status=DUTY_STATUS_ON_DUTY_NOT_DRIVING,
        label=label,
        duration_hours=duration_hours,
        citation=citation,
    )
    state.duty_window_hours += duration_hours
    state.cumulative_cycle_hours += duration_hours

    # 2020 FMCSA HOS Final Rule: On-duty non-driving of >= 30 mins satisfies the 30-min break
    if duration_hours >= HOS_BREAK_DURATION_HOURS:
        state.drive_since_break = 0.0


def simulate_trip(
    leg1_miles: float,
    leg1_hours: float,
    leg2_miles: float,
    leg2_hours: float,
    current_cycle_used_hrs: float,
    start_time: Optional[datetime] = None,
) -> List[Segment]:
    """
    Executes a complete FMCSA HOS forward simulation for a commercial freight haul.

    Args:
        leg1_miles: Origin to Shipper pickup mileage.
        leg1_hours: Driving hours to pickup.
        leg2_miles: Shipper to Receiver destination mileage.
        leg2_hours: Driving hours to destination.
        current_cycle_used_hrs: Cumulative duty hours logged in past 8 days (0-70).
        start_time: Departure timestamp. Defaults to current system datetime.

    Returns:
        List of continuous Segment objects describing the complete journey timeline.
    """
    if start_time is None:
        start_time = datetime.now().replace(minute=0, second=0, microsecond=0)

    initial_cycle = min(max(0.0, current_cycle_used_hrs), HOS_CYCLE_LIMIT_HOURS)
    state = SimulatorState(now=start_time, cumulative_cycle_hours=initial_cycle)

    # --------------------------------------------------------------------------
    # Leg 1: Current location -> Shipper (Pickup)
    # --------------------------------------------------------------------------
    leg1_chunks = _partition_leg_by_fuel_stops(leg1_miles, leg1_hours, state.cumulative_miles)
    for miles, hours, needs_fuel in leg1_chunks:
        _simulate_driving_chunk(state, miles, hours, "En Route to Pickup Location")
        if needs_fuel:
            _simulate_on_duty_stop(
                state,
                DEFAULT_FUEL_STOP_HOURS,
                "Fuel & Walk-Around Inspection Stop",
                citation="Fleet Policy",
            )

    # Cargo Pickup / Loading dock time
    _simulate_on_duty_stop(
        state,
        DEFAULT_PICKUP_HOURS,
        "Shipper Facility — Cargo Loading & Paperwork",
        citation="49 CFR § 395.2",
    )

    # --------------------------------------------------------------------------
    # Leg 2: Shipper (Pickup) -> Receiver (Drop-off)
    # --------------------------------------------------------------------------
    leg2_chunks = _partition_leg_by_fuel_stops(leg2_miles, leg2_hours, state.cumulative_miles)
    for miles, hours, needs_fuel in leg2_chunks:
        _simulate_driving_chunk(state, miles, hours, "En Route to Delivery Destination")
        if needs_fuel:
            _simulate_on_duty_stop(
                state,
                DEFAULT_FUEL_STOP_HOURS,
                "Fuel & Walk-Around Inspection Stop",
                citation="Fleet Policy",
            )

    # Cargo Delivery / Unloading dock time
    _simulate_on_duty_stop(
        state,
        DEFAULT_DROPOFF_HOURS,
        "Receiver Facility — Cargo Unloading & Sign-off",
        citation="49 CFR § 395.2",
    )

    return state.timeline


def build_daily_logs(timeline: List[Segment]) -> List[Dict[str, Any]]:
    """
    Partitions the continuous trip timeline into official FMCSA Form MCS-59
    calendar-day driver log sheets (00:00 to 24:00 midnight-to-midnight).

    Guarantees every day sheet totals exactly 24.0 hours with no unassigned gaps.
    """
    if not timeline:
        return []

    days: List[Dict[str, Any]] = []
    calendar_day_start = timeline[0].start.replace(hour=0, minute=0, second=0, microsecond=0)
    trip_end_time = timeline[-1].end

    day_idx = 1
    while calendar_day_start < trip_end_time or (calendar_day_start == trip_end_time and not days):
        calendar_day_end = calendar_day_start + timedelta(days=1)
        raw_segments: List[Dict[str, Any]] = []

        # Find all timeline segments that overlap this 24-hour day
        for seg in timeline:
            overlap_start = max(seg.start, calendar_day_start)
            overlap_end = min(seg.end, calendar_day_end)
            if overlap_end <= overlap_start:
                continue

            from_hr = (overlap_start - calendar_day_start).total_seconds() / 3600.0
            to_hr = (overlap_end - calendar_day_start).total_seconds() / 3600.0

            raw_segments.append({
                "status": seg.status,
                "from_hr": round(from_hr, 4),
                "to_hr": round(to_hr, 4),
                "duration_hours": round(to_hr - from_hr, 4),
                "label": seg.label,
                "citation": seg.citation,
            })

        # Ensure exact 24-hour continuity:
        # Prepend off-duty if trip begins after 00:00 on Day 1
        day_segments: List[Dict[str, Any]] = []
        if raw_segments and raw_segments[0]["from_hr"] > EPSILON:
            day_segments.append({
                "status": DUTY_STATUS_OFF_DUTY,
                "from_hr": 0.0,
                "to_hr": raw_segments[0]["from_hr"],
                "duration_hours": raw_segments[0]["from_hr"],
                "label": "Off-Duty Rest (Prior to Dispatch)",
                "citation": "49 CFR § 395.2",
            })

        day_segments.extend(raw_segments)

        # Append off-duty if trip ends before 24:00 on the final day
        if day_segments and day_segments[-1]["to_hr"] < 24.0 - EPSILON:
            final_to = day_segments[-1]["to_hr"]
            day_segments.append({
                "status": DUTY_STATUS_OFF_DUTY,
                "from_hr": final_to,
                "to_hr": 24.0,
                "duration_hours": round(24.0 - final_to, 4),
                "label": "Off-Duty Rest (Post Delivery)",
                "citation": "49 CFR § 395.2",
            })

        # If a day has no segments (e.g. edge boundary), create a full 24h off-duty day
        if not day_segments:
            day_segments.append({
                "status": DUTY_STATUS_OFF_DUTY,
                "from_hr": 0.0,
                "to_hr": 24.0,
                "duration_hours": 24.0,
                "label": "Off-Duty Rest",
                "citation": "49 CFR § 395.2",
            })

        # Calculate exact duty totals
        totals = {
            DUTY_STATUS_OFF_DUTY: 0.0,
            "sleeper": 0.0,
            DUTY_STATUS_DRIVING: 0.0,
            DUTY_STATUS_ON_DUTY_NOT_DRIVING: 0.0,
        }
        for s in day_segments:
            status_key = s["status"]
            totals[status_key] = totals.get(status_key, 0.0) + (s["to_hr"] - s["from_hr"])

        total_day_hours = sum(totals.values())

        # Compile chronological remarks for inspection review
        remarks = []
        for s in day_segments:
            remarks.append({
                "from_hr": s["from_hr"],
                "to_hr": s["to_hr"],
                "time_display": f"{_hours_to_clock(s['from_hr'])} - {_hours_to_clock(s['to_hr'])}",
                "duration_hours": round(s["duration_hours"], 2),
                "status": s["status"],
                "label": s["label"],
                "citation": s.get("citation"),
            })

        days.append({
            "day_number": day_idx,
            "date": calendar_day_start.strftime("%Y-%m-%d"),
            "formatted_date": calendar_day_start.strftime("%A, %B %d, %Y"),
            "segments": day_segments,
            "totals": {k: round(v, 2) for k, v in totals.items()},
            "total_day_hours": round(total_day_hours, 2),
            "remarks": remarks,
        })

        day_idx += 1
        calendar_day_start = calendar_day_end

    return days


def build_stops(timeline: List[Segment]) -> List[Dict[str, Any]]:
    """
    Extracts all intermediate stops (pickup, delivery, fueling, rest breaks, resets)
    for interactive map markers and dispatch timeline display.
    """
    category_map = {
        "Mandatory 30-Minute Rest Break": "rest_break",
        "10-Hour Daily Rest & Off-Duty Reset": "daily_reset",
        "34-Hour Restart (70-Hour Cycle Limit Reached)": "cycle_restart",
        "Fuel & Walk-Around Inspection Stop": "fuel",
        "Shipper Facility — Cargo Loading & Paperwork": "pickup",
        "Receiver Facility — Cargo Unloading & Sign-off": "dropoff",
    }

    stops: List[Dict[str, Any]] = []
    stop_number = 1

    for seg in timeline:
        if seg.status == DUTY_STATUS_DRIVING:
            continue

        stop_type = category_map.get(seg.label, "inspection")
        stops.append({
            "stop_number": stop_number,
            "type": stop_type,
            "label": seg.label,
            "status": seg.status,
            "start": seg.start.isoformat(),
            "end": seg.end.isoformat(),
            "start_time_formatted": seg.start.strftime("%I:%M %p"),
            "end_time_formatted": seg.end.strftime("%I:%M %p"),
            "duration_hours": round(seg.hours, 2),
            "cumulative_miles": round(seg.start_miles, 1),
            "citation": seg.citation,
        })
        stop_number += 1

    return stops


def _hours_to_clock(hour_float: float) -> str:
    """Converts a fractional hour of the day (0.0 to 24.0) to a standard 12-hour clock string."""
    h_int = int(math.floor(hour_float)) % 24
    minutes = int(round((hour_float - math.floor(hour_float)) * 60.0))
    if minutes >= 60:
        minutes = 0
        h_int = (h_int + 1) % 24

    period = "AM" if h_int < 12 else "PM"
    h12 = 12 if (h_int % 12 == 0) else (h_int % 12)
    return f"{h12}:{minutes:02d} {period}"
