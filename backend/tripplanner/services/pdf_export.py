"""
DOT Form MCS-59 PDF Generation Engine.
Produces official, printable Federal Motor Carrier Safety Administration (FMCSA)
Driver's Daily Log sheets compliant with 49 CFR § 395.8 using ReportLab.
"""

import io
from typing import Any, Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas


# Grid coordinate constants for Landscape Letter (792 x 612 pt)
PAGE_WIDTH, PAGE_HEIGHT = landscape(letter)

GRID_X = 140
GRID_Y = 320
GRID_W = 550
GRID_H = 130
ROW_H = GRID_H / 4.0
HOUR_W = GRID_W / 24.0

DUTY_ROWS = [
    ("off_duty", "1. OFF DUTY"),
    ("sleeper", "2. SLEEPER BERTH"),
    ("driving", "3. DRIVING"),
    ("on_duty", "4. ON DUTY (NOT DRIVING)"),
]


def _draw_mcs59_page(
    c: canvas.Canvas,
    day_data: Dict[str, Any],
    metadata: Dict[str, Any],
    trip_summary: Dict[str, Any],
) -> None:
    """
    Renders a single calendar day Form MCS-59 log sheet onto the PDF canvas.
    """
    # --------------------------------------------------------------------------
    # 1. Document Frame & Outer Border
    # --------------------------------------------------------------------------
    c.setLineWidth(1.5)
    c.setStrokeColor(colors.HexColor("#0f172a"))
    c.rect(20, 20, PAGE_WIDTH - 40, PAGE_HEIGHT - 40)

    # --------------------------------------------------------------------------
    # 2. Header Section
    # --------------------------------------------------------------------------
    carrier_name = metadata.get("carrier_name", "Apex Logistics Freight, Inc.")
    driver_name = metadata.get("driver_name", "Commercial Driver")
    truck_number = metadata.get("truck_number", "TRK-409")
    date_str = day_data.get("formatted_date", day_data.get("date", "Unknown Date"))
    day_num = day_data.get("day_number", 1)

    # Top Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(35, PAGE_HEIGHT - 48, "DRIVER'S DAILY LOG")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(35, PAGE_HEIGHT - 60, "FORM MCS-59 · U.S. DEPARTMENT OF TRANSPORTATION · 49 CFR § 395.8")

    # Day Badge
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(PAGE_WIDTH - 145, PAGE_HEIGHT - 62, 110, 26, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(PAGE_WIDTH - 90, PAGE_HEIGHT - 50, f"DAY {day_num} OF {trip_summary.get('total_days', 1)}")

    # Adverse Driving Conditions Audit Badge
    if day_data.get("adverse_conditions_claimed") or metadata.get("adverse_conditions_claimed"):
        c.setFillColor(colors.HexColor("#d97706"))
        c.rect(PAGE_WIDTH - 355, PAGE_HEIGHT - 62, 202, 26, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(PAGE_WIDTH - 254, PAGE_HEIGHT - 50, "49 CFR § 395.1(b) ADVERSE EXCEPTION")

    # Carrier & Equipment Meta Box
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(0.8)
    c.rect(35, PAGE_HEIGHT - 118, PAGE_WIDTH - 70, 50, fill=True, stroke=True)

    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(45, PAGE_HEIGHT - 82, "Operating Carrier:")
    c.setFont("Helvetica", 9)
    c.drawString(135, PAGE_HEIGHT - 82, carrier_name)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(45, PAGE_HEIGHT - 100, "Driver Name:")
    c.setFont("Helvetica", 9)
    c.drawString(135, PAGE_HEIGHT - 100, driver_name)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(380, PAGE_HEIGHT - 82, "Log Date:")
    c.setFont("Helvetica", 9)
    c.drawString(440, PAGE_HEIGHT - 82, date_str)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(380, PAGE_HEIGHT - 100, "Vehicle / Tractor #:")
    c.setFont("Helvetica", 9)
    c.drawString(480, PAGE_HEIGHT - 100, truck_number)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(580, PAGE_HEIGHT - 82, "24-Hr Period Starting:")
    c.setFont("Helvetica", 9)
    c.drawString(695, PAGE_HEIGHT - 82, "Midnight (00:00)")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(580, PAGE_HEIGHT - 100, "HOS Rule Set:")
    c.setFont("Helvetica", 9)
    c.drawString(660, PAGE_HEIGHT - 100, "70-Hr / 8-Day Property")

    # --------------------------------------------------------------------------
    # 3. 24-Hour Duty Status Grid (4 Rows x 24 Hours)
    # --------------------------------------------------------------------------
    # Grid background
    c.setFillColor(colors.HexColor("#ffffff"))
    c.rect(GRID_X, GRID_Y, GRID_W, GRID_H, fill=True, stroke=True)

    # 15-minute sub-ticks & Hour lines
    for h in range(25):
        x = GRID_X + h * HOUR_W
        is_major = h % 6 == 0
        c.setStrokeColor(colors.HexColor("#475569" if is_major else "#cbd5e1"))
        c.setLineWidth(1.0 if is_major else 0.5)
        c.line(x, GRID_Y, x, GRID_Y + GRID_H)

        # Top hour labels
        c.setFont("Helvetica-Bold" if is_major else "Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#0f172a"))
        label = "Mid" if (h == 0 or h == 24) else ("Noon" if h == 12 else str(h > 12 and h - 12 or h))
        c.drawCentredString(x, GRID_Y + GRID_H + 4, label)

        # 15-minute sub-ticks (between hours)
        if h < 24:
            for q in range(1, 4):
                qx = x + q * (HOUR_W / 4.0)
                c.setStrokeColor(colors.HexColor("#e2e8f0"))
                c.setLineWidth(0.4)
                c.line(qx, GRID_Y, qx, GRID_Y + GRID_H)

    # Horizontal row lines and Row Labels
    for idx, (key, row_title) in enumerate(DUTY_ROWS):
        y_bottom = GRID_Y + (3 - idx) * ROW_H
        y_mid = y_bottom + ROW_H / 2.0

        if idx > 0:
            c.setStrokeColor(colors.HexColor("#94a3b8"))
            c.setLineWidth(0.8)
            c.line(GRID_X, y_bottom + ROW_H, GRID_X + GRID_W, y_bottom + ROW_H)

        # Row label on left
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.HexColor("#0f172a"))
        c.drawRightString(GRID_X - 10, y_mid - 3, row_title)

        # Row total on right
        row_hours = day_data.get("totals", {}).get(key, 0.0)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(GRID_X + GRID_W + 28, y_mid - 3, f"{row_hours:.1f}h")

    # Header for totals column
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(GRID_X + GRID_W + 28, GRID_Y + GRID_H + 4, "TOTAL")

    # --------------------------------------------------------------------------
    # 4. Driver's Status Stepped Polyline
    # --------------------------------------------------------------------------
    segments = day_data.get("segments", [])
    row_map = {"off_duty": 0, "sleeper": 1, "driving": 2, "on_duty": 3}

    if segments:
        c.setStrokeColor(colors.HexColor("#0f172a"))
        c.setLineWidth(2.2)
        c.setLineJoin(1)  # Miter

        last_x = None
        last_y = None

        for s_idx, seg in enumerate(segments):
            r_idx = row_map.get(seg.get("status"), 0)
            y = GRID_Y + (3 - r_idx) * ROW_H + ROW_H / 2.0
            x1 = GRID_X + seg.get("from_hr", 0.0) * HOUR_W
            x2 = GRID_X + seg.get("to_hr", 0.0) * HOUR_W

            if last_x is not None and last_y is not None:
                # Vertical transition from previous row to current row
                c.line(last_x, last_y, x1, y)

            # Horizontal status line
            c.line(x1, y, x2, y)
            last_x = x2
            last_y = y

    # Total Verification Bar
    total_day_hours = sum(day_data.get("totals", {}).values())
    c.setFillColor(colors.HexColor("#ecfdf5"))
    c.setStrokeColor(colors.HexColor("#6ee7b7"))
    c.setLineWidth(0.8)
    c.rect(GRID_X, GRID_Y - 22, GRID_W + 55, 18, fill=True, stroke=True)

    c.setFillColor(colors.HexColor("#065f46"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(
        GRID_X + 10,
        GRID_Y - 16,
        f"TOTAL HOURS: {total_day_hours:.1f} / 24.0 Verified  |  Off Duty: {day_data['totals'].get('off_duty',0):.1f}h  |  "
        f"Sleeper: {day_data['totals'].get('sleeper',0):.1f}h  |  Driving: {day_data['totals'].get('driving',0):.1f}h  |  "
        f"On Duty: {day_data['totals'].get('on_duty',0):.1f}h"
    )

    # --------------------------------------------------------------------------
    # 5. Chronological Duty & Remarks Table
    # --------------------------------------------------------------------------
    tbl_top = GRID_Y - 34
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(35, tbl_top, "REMARKS & RECORD OF DUTY STATUS CHANGES")

    # Table Header
    th_y = tbl_top - 14
    c.setFillColor(colors.HexColor("#f1f5f9"))
    c.rect(35, th_y - 2, PAGE_WIDTH - 70, 14, fill=True, stroke=False)
    c.setFillColor(colors.HexColor("#334155"))
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(42, th_y + 2, "TIME RANGE")
    c.drawString(145, th_y + 2, "HRS")
    c.drawString(185, th_y + 2, "STATUS")
    c.drawString(320, th_y + 2, "ACTIVITY / LOCATION REMARKS")
    c.drawString(640, th_y + 2, "CFR CITATION")

    # Table rows (up to 7 remarks on page)
    row_y = th_y - 14
    c.setFont("Helvetica", 7.5)
    for r_idx, seg in enumerate(segments[:8]):
        c.setFillColor(colors.HexColor("#f8fafc" if r_idx % 2 == 0 else "#ffffff"))
        c.rect(35, row_y - 2, PAGE_WIDTH - 70, 12, fill=True, stroke=False)

        c.setFillColor(colors.HexColor("#0f172a"))
        time_str = f"{_hr_to_clock(seg.get('from_hr', 0))} - {_hr_to_clock(seg.get('to_hr', 0))}"
        c.drawString(42, row_y + 1, time_str)
        c.drawString(145, row_y + 1, f"{seg.get('duration_hours', 0):.1f}h")
        c.drawString(185, row_y + 1, seg.get("status", "").replace("_", " ").upper())

        label_txt = seg.get("label", "")
        if len(label_txt) > 60:
            label_txt = label_txt[:57] + "..."
        c.drawString(320, row_y + 1, label_txt)
        c.drawString(640, row_y + 1, seg.get("citation", "49 CFR § 395"))

        row_y -= 13

    # --------------------------------------------------------------------------
    # 6. Driver Certification & Signature Block
    # --------------------------------------------------------------------------
    cert_y = 62
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(0.8)
    c.line(35, cert_y + 24, PAGE_WIDTH - 35, cert_y + 24)

    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(
        35,
        cert_y + 12,
        "I certify that these entries are a true and accurate record of my duty status and driving hours in accordance with 49 CFR Part 395."
    )

    # Signature Lines
    c.setStrokeColor(colors.HexColor("#475569"))
    c.setLineWidth(0.8)

    c.line(35, cert_y - 10, 260, cert_y - 10)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(35, cert_y - 20, "DRIVER SIGNATURE: " + driver_name)

    c.line(300, cert_y - 10, 480, cert_y - 10)
    c.drawString(300, cert_y - 20, "DATE OF SUBMISSION")

    c.line(520, cert_y - 10, PAGE_WIDTH - 35, cert_y - 10)
    c.drawString(520, cert_y - 20, "CARRIER AUDIT & COMPLIANCE VERIFICATION")


def generate_mcs59_pdf(
    trip_data: Dict[str, Any],
    target_day: int = None,
) -> bytes:
    """
    Generates a complete multi-page or single-day Form MCS-59 PDF document.

    Args:
        trip_data: The full trip result payload.
        target_day: Optional day number to generate. If None, generates all days.

    Returns:
        bytes: Raw PDF document binary.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))

    daily_logs = trip_data.get("daily_logs", [])
    metadata = trip_data.get("metadata", {})
    summary = trip_data.get("summary", {})

    if target_day is not None:
        daily_logs = [d for d in daily_logs if d.get("day_number") == target_day]
        if not daily_logs and trip_data.get("daily_logs"):
            daily_logs = [trip_data["daily_logs"][0]]

    for idx, day in enumerate(daily_logs):
        if idx > 0:
            c.showPage()
        _draw_mcs59_page(c, day, metadata, summary)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def _hr_to_clock(hour_float: float) -> str:
    h = int(hour_float) % 24
    m = int(round((hour_float - int(hour_float)) * 60))
    if m >= 60:
        m = 0
        h = (h + 1) % 24
    period = "AM" if h < 12 else "PM"
    h12 = 12 if (h % 12 == 0) else (h % 12)
    return f"{h12}:{m:02d} {period}"

