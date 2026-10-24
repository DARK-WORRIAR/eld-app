import React, { useState } from "react";

const QUICK_CORRIDORS = [
  {
    name: "Dallas → Chicago",
    current: "Dallas, TX",
    pickup: "Oklahoma City, OK",
    dropoff: "Chicago, IL",
    cycle: 10,
  },
  {
    name: "Atlanta → Los Angeles",
    current: "Atlanta, GA",
    pickup: "Memphis, TN",
    dropoff: "Los Angeles, CA",
    cycle: 18,
  },
  {
    name: "Seattle → Denver",
    current: "Seattle, WA",
    pickup: "Boise, ID",
    dropoff: "Denver, CO",
    cycle: 14,
  },
  {
    name: "Philly → Jacksonville",
    current: "Philadelphia, PA",
    pickup: "Richmond, VA",
    dropoff: "Jacksonville, FL",
    cycle: 8,
  },
];

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    current_location: "Dallas, TX",
    pickup_location: "Oklahoma City, OK",
    dropoff_location: "Chicago, IL",
    current_cycle_used_hrs: "12",
    departure_date: new Date().toISOString().slice(0, 10),
    departure_time: "07:00",
    adverse_conditions_claimed: false,
    adverse_conditions_reason: "",
    driver_name: "Marcus Vance",
    carrier_name: "Apex Logistics Freight, Inc.",
    truck_number: "TRK-840",
  });

  const [showMetadata, setShowMetadata] = useState(false);
  const [validationError, setValidationError] = useState(null);

  function updateField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (validationError) setValidationError(null);
  }

  function handleQuickLoad(preset) {
    setForm((prev) => ({
      ...prev,
      current_location: preset.current,
      pickup_location: preset.pickup,
      dropoff_location: preset.dropoff,
      current_cycle_used_hrs: String(preset.cycle),
    }));
    setValidationError(null);
  }

  function handleFormSubmit(e) {
    e.preventDefault();
    setValidationError(null);

    const current = form.current_location.trim();
    const pickup = form.pickup_location.trim();
    const dropoff = form.dropoff_location.trim();

    if (!current || !pickup || !dropoff) {
      setValidationError("All three routing locations (Origin, Pickup, Drop-off) are required.");
      return;
    }

    if (pickup.toLowerCase() === dropoff.toLowerCase()) {
      setValidationError("Pickup location and Drop-off location cannot be identical.");
      return;
    }

    const cycleHrs = Number(form.current_cycle_used_hrs);
    if (isNaN(cycleHrs) || cycleHrs < 0 || cycleHrs > 70) {
      setValidationError("Current cycle hours must be a valid number between 0.0 and 70.0 hours.");
      return;
    }

    let startIso = null;
    if (form.departure_date && form.departure_time) {
      try {
        const dt = new Date(`${form.departure_date}T${form.departure_time}:00`);
        if (!isNaN(dt.getTime())) {
          startIso = dt.toISOString();
        }
      } catch {
        // fallback to server default
      }
    }

    onSubmit({
      current_location: current,
      pickup_location: pickup,
      dropoff_location: dropoff,
      current_cycle_used_hrs: cycleHrs,
      start_time: startIso,
      adverse_conditions_claimed: Boolean(form.adverse_conditions_claimed),
      adverse_conditions_reason: form.adverse_conditions_claimed
        ? (form.adverse_conditions_reason.trim() || "Unforeseen adverse weather/road condition")
        : "",
      driver_name: form.driver_name.trim() || "Commercial Driver",
      carrier_name: form.carrier_name.trim() || "Apex Logistics Freight, Inc.",
      truck_number: form.truck_number.trim() || "TRK-409",
    });
  }

  const cycleNum = Number(form.current_cycle_used_hrs) || 0;
  const cycleAvailable = Math.max(0, 70 - cycleNum);

  return (
    <form className="trip-form" onSubmit={handleFormSubmit} noValidate>
      <div className="trip-form__eyebrow">Dispatch Console</div>
      <h1 className="trip-form__title">Commercial Trip Planner</h1>
      <p className="trip-form__subtitle">
        Automated corridor routing, FMCSA Hours-of-Service simulation, and Form MCS-59 daily log generation.
      </p>

      {/* Quick Corridor Presets */}
      <div className="trip-form__presets">
        <span className="trip-form__presets-label">Freight Corridors:</span>
        <div className="trip-form__presets-list">
          {QUICK_CORRIDORS.map((c) => (
            <button
              key={c.name}
              type="button"
              className="trip-form__preset-btn"
              onClick={() => handleQuickLoad(c)}
              title={`Load corridor ${c.current} -> ${c.pickup} -> ${c.dropoff}`}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {/* Waypoint inputs */}
      <div className="trip-form__section">
        <label className="trip-form__field">
          <span className="trip-form__label">
            <span className="trip-form__dot trip-form__dot--origin"></span> Current Location (Origin)
          </span>
          <input
            type="text"
            className="trip-form__input"
            placeholder="City, State or Address (e.g. Dallas, TX)"
            value={form.current_location}
            onChange={(e) => updateField("current_location", e.target.value)}
            required
          />
        </label>

        <label className="trip-form__field">
          <span className="trip-form__label">
            <span className="trip-form__dot trip-form__dot--pickup"></span> Shipper Facility (Pickup)
          </span>
          <input
            type="text"
            className="trip-form__input"
            placeholder="City, State or Address (e.g. Oklahoma City, OK)"
            value={form.pickup_location}
            onChange={(e) => updateField("pickup_location", e.target.value)}
            required
          />
        </label>

        <label className="trip-form__field">
          <span className="trip-form__label">
            <span className="trip-form__dot trip-form__dot--dropoff"></span> Receiver Facility (Drop-off)
          </span>
          <input
            type="text"
            className="trip-form__input"
            placeholder="City, State or Address (e.g. Chicago, IL)"
            value={form.dropoff_location}
            onChange={(e) => updateField("dropoff_location", e.target.value)}
            required
          />
        </label>
      </div>

      {/* Cycle Hours Gauge */}
      <div className="trip-form__section">
        <label className="trip-form__field">
          <div className="trip-form__field-split">
            <span className="trip-form__label">Prior Cycle Hours Logged</span>
            <span className="trip-form__badge-metric">{cycleNum.toFixed(1)} / 70.0 hrs</span>
          </div>
          <input
            type="number"
            min="0"
            max="70"
            step="0.5"
            className="trip-form__input"
            value={form.current_cycle_used_hrs}
            onChange={(e) => updateField("current_cycle_used_hrs", e.target.value)}
            required
          />
        </label>

        <div className="trip-form__cycle-bar-wrap">
          <div
            className={`trip-form__cycle-bar ${cycleNum > 60 ? "trip-form__cycle-bar--warning" : ""}`}
            style={{ width: `${Math.min(100, (cycleNum / 70) * 100)}%` }}
          ></div>
        </div>
        <div className="trip-form__cycle-helper">
          <span>{cycleAvailable.toFixed(1)} hrs capacity remaining</span>
          {cycleNum > 60 && <span className="trip-form__cycle-alert">Near 70h cycle limit</span>}
        </div>
      </div>

      {/* Planned Departure Schedule */}
      <div className="trip-form__section">
        <div className="trip-form__row">
          <label className="trip-form__field trip-form__field--half">
            <span className="trip-form__label">Departure Date</span>
            <input
              type="date"
              className="trip-form__input"
              value={form.departure_date}
              onChange={(e) => updateField("departure_date", e.target.value)}
            />
          </label>
          <label className="trip-form__field trip-form__field--half">
            <span className="trip-form__label">Departure Time</span>
            <input
              type="time"
              className="trip-form__input"
              value={form.departure_time}
              onChange={(e) => updateField("departure_time", e.target.value)}
            />
          </label>
        </div>
      </div>

      {/* Adverse Driving Conditions Exception (49 CFR § 395.1(b)) */}
      <div className="trip-form__adverse-card">
        <label className="trip-form__checkbox-label">
          <input
            type="checkbox"
            className="trip-form__checkbox"
            checked={form.adverse_conditions_claimed}
            onChange={(e) => updateField("adverse_conditions_claimed", e.target.checked)}
          />
          <span className="trip-form__checkbox-text">
            <strong>Claim Adverse Driving Conditions (+2 hrs)</strong>
            <small>49 CFR § 395.1(b)(1) — Extends driving limit to 13h &amp; duty window to 16h for unforeseen road/weather events.</small>
          </span>
        </label>

        {form.adverse_conditions_claimed && (
          <div className="trip-form__adverse-input-wrap">
            <label className="trip-form__field">
              <span className="trip-form__label">Adverse Condition Reason (Required for DOT Audit)</span>
              <input
                type="text"
                className="trip-form__input"
                placeholder="e.g. Unforeseen blizzard highway closure on I-80"
                value={form.adverse_conditions_reason}
                onChange={(e) => updateField("adverse_conditions_reason", e.target.value)}
              />
            </label>
          </div>
        )}
      </div>

      {/* Collapsible Fleet Metadata */}
      <div className="trip-form__metadata-toggle">
        <button
          type="button"
          className="trip-form__toggle-btn"
          onClick={() => setShowMetadata((v) => !v)}
        >
          <span>{showMetadata ? "▼" : "▶"} Carrier &amp; Equipment Metadata</span>
          <span className="trip-form__toggle-sub">For Form MCS-59 Log Headers</span>
        </button>

        {showMetadata && (
          <div className="trip-form__metadata-body">
            <label className="trip-form__field">
              <span className="trip-form__label">Driver Name</span>
              <input
                type="text"
                className="trip-form__input"
                value={form.driver_name}
                onChange={(e) => updateField("driver_name", e.target.value)}
              />
            </label>
            <label className="trip-form__field">
              <span className="trip-form__label">Operating Motor Carrier</span>
              <input
                type="text"
                className="trip-form__input"
                value={form.carrier_name}
                onChange={(e) => updateField("carrier_name", e.target.value)}
              />
            </label>
            <label className="trip-form__field">
              <span className="trip-form__label">Tractor / Unit ID</span>
              <input
                type="text"
                className="trip-form__input"
                value={form.truck_number}
                onChange={(e) => updateField("truck_number", e.target.value)}
              />
            </label>
          </div>
        )}
      </div>

      {validationError && <div className="trip-form__error">{validationError}</div>}

      <button className="trip-form__submit" type="submit" disabled={loading}>
        {loading ? (
          <span className="trip-form__submit-spinner">
            <span className="trip-form__spin-icon">◈</span> Calculating HOS Route...
          </span>
        ) : (
          "Calculate Dispatch & Logs"
        )}
      </button>

      {/* Regulatory Notice & Compliance Assumptions */}
      <div className="trip-form__regulations">
        <div className="trip-form__regulations-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          FMCSA Standard 49 CFR Part 395 Modeled
        </div>
        <ul>
          <li><strong>11-Hour Driving Rule:</strong> 49 CFR § 395.3(a)(3)(i)</li>
          <li><strong>14-Hour Duty Window:</strong> 49 CFR § 395.3(a)(2)</li>
          <li><strong>30-Min Rest Break:</strong> After 8 cumulative driving hours</li>
          <li><strong>10-Hour Off-Duty Reset:</strong> 49 CFR § 395.3(a)(1)</li>
          <li><strong>70-Hr / 8-Day Cycle:</strong> 34-hour restart on limit breach</li>
          <li><strong>Fuel Stops:</strong> Scheduled at 1,000-mile highway intervals</li>
        </ul>
      </div>
    </form>
  );
}
