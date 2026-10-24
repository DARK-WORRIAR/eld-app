# HAUL LOG — Commercial Fleet Dispatch & ELD Compliance Engine

[![FMCSA 49 CFR Part 395 Compliant](https://img.shields.io/badge/FMCSA-49%20CFR%20%C2%A7%20395-blue.svg)](https://www.fcmcsa.dot.gov/regulations/hours-of-service)
[![Django REST Framework](https://img.shields.io/badge/Django-5.0%20%7C%20DRF-green.svg)](https://www.django-rest-framework.org/)
[![React 18](https://img.shields.io/badge/React-18%20%7C%20Vite-61dafb.svg)](https://react.dev/)
[![Test Suite](https://img.shields.io/badge/Tests-Passing%20(18%2F18)-brightgreen.svg)]()

**HAUL LOG** is a full-stack logistics dispatch and compliance platform engineered for commercial motor carriers. It calculates highway freight corridors, enforces Federal Motor Carrier Safety Administration (FMCSA) Hours-of-Service (HOS) property-carrying driver regulations under **49 CFR Part 395**, schedules required fueling and inspection stops, and dynamically renders official **Form MCS-59 Driver's Daily Log sheets** (24-hour midnight-to-midnight status grids).

---

## Architecture Overview

```
eld-app/
├── backend/                  # Django REST Framework application
│   ├── config/               # Project configuration, WSGI/ASGI, WhiteNoise settings
│   ├── tripplanner/          # Core logistics and compliance domain
│   │   ├── services/         # Domain services layer
│   │   │   ├── constants.py  # Regulatory constants (49 CFR Part 395)
│   │   │   ├── hos.py        # HOS simulation and 24-hr daily log segmentation
│   │   │   ├── pdf_export.py # DOT Form MCS-59 ReportLab PDF rendering engine
│   │   │   ├── routing.py    # OSRM corridor calculation & Haversine projection
│   │   │   └── geocode.py    # Caching forward geocoding (Nominatim & Photon)
│   │   ├── tests/            # Automated test suite (HOS, views, routing)
│   │   ├── models.py         # Persistent dispatch records and metadata
│   │   ├── serializers.py    # Request validation schemas
│   │   └── views.py          # API controllers & health endpoints
│   ├── manage.py
│   └── requirements.txt
└── frontend/                 # React 18 single-page cockpit (Vite)
    ├── src/
    │   ├── components/
    │   │   ├── Navbar.jsx            # Operations navigation and status
    │   │   ├── TripForm.jsx          # Dispatch input & freight corridor presets
    │   │   ├── SummaryBar.jsx        # Key operational & compliance metrics
    │   │   ├── RouteMap.jsx          # Leaflet interactive corridor visualizer
    │   │   ├── StopsTimeline.jsx     # Chronological stop sequence & badges
    │   │   ├── DailyLogSheet.jsx     # FMCSA Form MCS-59 24-hour SVG grid
    │   │   └── TripHistoryModal.jsx  # Past dispatch drawer & loader
    │   ├── api.js                    # Resilient typed API client
    │   ├── App.jsx                   # Master dashboard state controller
    │   └── App.css                   # Enterprise cockpit design system & print styles
    ├── package.json
    └── vite.config.js
```

---

## FMCSA Hours-of-Service (HOS) Engine

The simulation engine in `backend/tripplanner/services/hos.py` models real-world commercial trucking constraints under **49 CFR Part 395** for property-carrying drivers operating under the **70-hour / 8-day cycle**:

| Regulation | CFR Citation | Implementation in Engine |
| :--- | :--- | :--- |
| **11-Hour Driving Limit** | § 395.3(a)(3)(i) | Driving is interrupted when 11 cumulative driving hours are reached following 10 consecutive hours off-duty. |
| **14-Hour Duty Window** | § 395.3(a)(2) | Driving is prohibited after the 14th consecutive hour from coming on duty. Off-duty rest breaks do not extend this clock. |
| **30-Minute Rest Break** | § 395.3(a)(3)(ii) | A mandatory 30-minute break is scheduled before driving exceeds 8 cumulative hours without interruption. |
| **10-Hour Daily Reset** | § 395.3(a)(1) | When the 11-hour driving or 14-hour window limit is reached, a 10 consecutive hour off-duty period resets both clocks. |
| **70-Hour / 8-Day Limit** | § 395.3(b)(2) | Driver duty time across the journey cannot exceed 70 on-duty hours in any 8-day rolling cycle. |
| **34-Hour Restart** | § 395.3(d) | If cumulative duty hours reach 70.0, a 34 consecutive hour restart period resets the cycle clock to zero. |
| **Fueling Stops** | Fleet Standard | Fuel stops (30 min On-Duty) are scheduled at 1,000-mile highway intervals. |
| **Terminal Operations** | Fleet Standard | 1.0 hour On-Duty (not driving) is allotted for cargo loading at pickup and unloading at drop-off. |

### Form MCS-59 Grid Continuity
In accordance with FMCSA inspection standards, every calendar-day log sheet spans **exactly 24.0 hours (00:00 to 24:00)**:
- Pre-dispatch intervals before scheduled departure are accounted for as Off-Duty rest.
- Post-delivery intervals after final unloading are accounted for as Off-Duty rest.
- The 4 duty status rows (`1. Off Duty`, `2. Sleeper Berth`, `3. Driving`, `4. On Duty Not Driving`) are connected by a single continuous step-function status line with no unassigned gaps.

---

## API Specifications

### 1. Plan Trip Dispatch
`POST /api/plan-trip/`

Computes route coordinates, enforces HOS rules, schedules stops, and generates MCS-59 log grids.

**Request Payload:**
```json
{
  "current_location": "Dallas, TX",
  "pickup_location": "Oklahoma City, OK",
  "dropoff_location": "Chicago, IL",
  "current_cycle_used_hrs": 12.0,
  "start_time": "2026-10-23T07:00:00Z",
  "driver_name": "Marcus Vance",
  "carrier_name": "Apex Logistics Freight, Inc.",
  "truck_number": "TRK-840"
}
```

**Response (200 OK):**
```json
{
  "trip_id": 4,
  "metadata": {
    "driver_name": "Marcus Vance",
    "carrier_name": "Apex Logistics Freight, Inc.",
    "truck_number": "TRK-840",
    "dispatch_time": "2026-10-23T07:00:00Z",
    "regulations_standard": "49 CFR Part 395 Property-Carrying Driver Rules"
  },
  "locations": {
    "current": { "lat": 32.7767, "lon": -96.7970, "display_name": "Dallas, Texas, United States" },
    "pickup": { "lat": 35.4676, "lon": -97.5164, "display_name": "Oklahoma City, Oklahoma, United States" },
    "dropoff": { "lat": 41.8781, "lon": -87.6298, "display_name": "Chicago, Illinois, United States" }
  },
  "route": {
    "geometry": [[32.7767, -96.7970], "..."],
    "total_distance_miles": 1012.4,
    "total_duration_hours": 15.6,
    "legs": [...]
  },
  "stops": [
    {
      "stop_number": 1,
      "type": "pickup",
      "label": "Shipper Facility — Cargo Loading & Paperwork",
      "duration_hours": 1.0,
      "cumulative_miles": 206.1,
      "position": [35.4676, -97.5164],
      "citation": "49 CFR § 395.2"
    }
  ],
  "daily_logs": [
    {
      "day_number": 1,
      "date": "2026-10-23",
      "formatted_date": "Friday, October 23, 2026",
      "total_day_hours": 24.0,
      "totals": { "off_duty": 11.5, "sleeper": 0.0, "driving": 10.5, "on_duty": 2.0 },
      "segments": [...],
      "remarks": [...]
    }
  ],
  "summary": {
    "total_days": 2,
    "total_distance_miles": 1012.4,
    "total_drive_hours": 15.6,
    "total_on_duty_hours": 2.0,
    "compliance_status": "Fully Compliant with FMCSA 49 CFR § 395"
  }
}
```

### 2. Form MCS-59 PDF Export
- `GET /api/trips/{id}/pdf/`: Streams a downloadable, official Form MCS-59 PDF file for all days (or `?day=<int>` for a specific day).
- `POST /api/export-pdf/`: Directly renders and returns a Form MCS-59 PDF from any active dispatch JSON payload.

### 3. Historical Trips
- `GET /api/trips/`: Returns list of recently planned dispatches.
- `GET /api/trips/{id}/`: Returns full detail payload for a specific trip record.

### 4. Health Check
- `GET /api/health/`: Returns service status and database heartbeat.

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Backend Service
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations and collect static assets
python manage.py migrate
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver 8000
```
API runs at `http://localhost:8000`. Test health: `http://localhost:8000/api/health/`

### 2. Frontend Application
```bash
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
UI runs at `http://localhost:5173`.

---

## Automated Test Suite

The test suite validates compliance edge cases, HOS reset triggers, and API schemas:

```bash
cd backend
python manage.py test
```

**Test Coverage Highlights:**
- `HostSimulationTests`:
  - 11-hour driving limit triggering 10-hour off-duty resets.
  - 14-hour duty window enforcement.
  - Mandatory 30-minute rest breaks after 8 cumulative driving hours.
  - 70-hour / 8-day cycle limit triggering 34-hour restarts.
  - 1,000-mile highway interval fuel stops.
  - Mathematical integrity of Form MCS-59 sheets (all days sum to 24.0 hours).
- `TripApiTests`:
  - Serialization boundary validation.
  - Health check verification.
  - Persistence and history retrieval.
- `RoutingAlgorithmTests`:
  - Spherical Haversine distance calculations.
  - Polyline segment coordinate interpolation.

---

## Production Deployment

### Environment Variables
Configure the following in your production environment (e.g., Render, Docker, Heroku):

| Variable | Description | Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | Cryptographically secure Django secret key | `production-key-random-bytes` |
| `DEBUG` | Enable/disable debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-delimited list of hostnames | `.onrender.com,api.yourdomain.com` |
| `CORS_ALLOWED_ORIGINS` | Comma-delimited list of frontend origins | `https://your-app.vercel.app` |
| `CORS_ALLOW_ALL` | Allow all CORS origins (development only) | `False` |

### Production Run Command
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```
Static assets are automatically served via **WhiteNoise** with compression and cache headers.

---

## Compliance Disclaimer

This application simulates property-carrying regulations under 49 CFR Part 395 for pre-trip dispatch planning and informational purposes. Operating commercial motor vehicle drivers must remain in compliance with all relevant federal, state, and local Department of Transportation (DOT) regulations.
