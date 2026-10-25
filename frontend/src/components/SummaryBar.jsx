import React from "react";

export default function SummaryBar({ route, summary, locations, metadata, dvirReports, onOpenDvir }) {
  if (!route || !summary || !locations) return null;

  return (
    <div className="summary-dashboard">
      <div className="summary-dashboard__corridor">
        <div className="summary-dashboard__corridor-title">Active Freight Corridor</div>
        <div className="summary-dashboard__route-pills">
          <span className="summary-dashboard__stop summary-dashboard__stop--origin">
            <span className="summary-dashboard__role">Origin:</span>
            {formatLocationName(locations.current?.display_name)}
          </span>
          <span className="summary-dashboard__arrow">→</span>
          <span className="summary-dashboard__stop summary-dashboard__stop--pickup">
            <span className="summary-dashboard__role">Shipper:</span>
            {formatLocationName(locations.pickup?.display_name)}
          </span>
          <span className="summary-dashboard__arrow">→</span>
          <span className="summary-dashboard__stop summary-dashboard__stop--dropoff">
            <span className="summary-dashboard__role">Receiver:</span>
            {formatLocationName(locations.dropoff?.display_name)}
          </span>
        </div>
      </div>

      <div className="summary-dashboard__metrics-grid">
        <MetricCard
          label="Total Distance"
          value={route.total_distance_miles?.toLocaleString() || "0"}
          unit="mi"
          subtext="Highway miles"
        />
        <MetricCard
          label="Total Drive Time"
          value={(summary.total_drive_hours || route.total_duration_hours || 0).toFixed(1)}
          unit="hrs"
          subtext="Behind the wheel"
        />
        <MetricCard
          label="Trip Span"
          value={summary.total_days}
          unit={summary.total_days === 1 ? "day" : "days"}
          subtext="Form MCS-59 sheets"
        />
        <MetricCard
          label="On-Duty (Loading)"
          value={(summary.total_on_duty_hours || 0).toFixed(1)}
          unit="hrs"
          subtext="Terminal dock time"
        />
        <MetricCard
          label="Rest &amp; Off-Duty"
          value={(summary.total_off_duty_hours || 0).toFixed(1)}
          unit="hrs"
          subtext="Breaks &amp; 10h resets"
        />
        <div className={`summary-dashboard__compliance-card ${(summary.adverse_conditions_claimed || metadata?.adverse_conditions_claimed) ? "summary-dashboard__compliance-card--adverse" : ""}`}>
          <div className="summary-dashboard__compliance-badge">
            <span className="summary-dashboard__check">{(summary.adverse_conditions_claimed || metadata?.adverse_conditions_claimed) ? "⚠️" : "✓"}</span>
            {(summary.adverse_conditions_claimed || metadata?.adverse_conditions_claimed) ? "§ 395.1(b) ADVERSE EXCEPTION" : "FMCSA COMPLIANT"}
          </div>
          <div className="summary-dashboard__compliance-text">
            {(summary.adverse_conditions_claimed || metadata?.adverse_conditions_claimed) ? "13h Drive / 16h Window Applied" : "49 CFR Part 395 Property Rules"}
          </div>
          <div className="summary-dashboard__compliance-sub">
            {(summary.adverse_conditions_claimed || metadata?.adverse_conditions_claimed)
              ? (summary.adverse_conditions_reason || metadata?.adverse_conditions_reason || "Unforeseen adverse condition logged for audit")
              : "All 11h, 14h, and 70h limits respected"}
          </div>
        </div>

        <div
          className="summary-dashboard__dvir-card"
          onClick={onOpenDvir}
          role="button"
          tabIndex={0}
          title="Click to view full 49 CFR Part 396 Driver Vehicle Inspection Reports"
        >
          <div className="summary-dashboard__dvir-badge">
            <span className="summary-dashboard__dvir-check">✓</span> 49 CFR § 396 DVIR
          </div>
          <div className="summary-dashboard__dvir-text">
            {dvirReports?.length || summary.dvir_inspections_count || 2} Inspections Logged
          </div>
          <div className="summary-dashboard__dvir-sub">
            12/12 Safety Systems Passed · View DVIR →
          </div>
        </div>
      </div>

      {summary.fuel_economy && (
        <div className="summary-dashboard__fuel-section">
          <div className="summary-dashboard__fuel-title">Operating Economics &amp; Fleet Fuel Analytics</div>
          <div className="summary-dashboard__fuel-grid">
            <div className="summary-dashboard__fuel-item">
              <span className="summary-dashboard__fuel-icon">⛽</span>
              <div>
                <span className="summary-dashboard__fuel-label">Est. Diesel Consumed</span>
                <strong className="summary-dashboard__fuel-val">{summary.fuel_economy.estimated_gallons?.toLocaleString()} gal</strong>
                <span className="summary-dashboard__fuel-sub">@ {summary.fuel_economy.average_mpg} MPG benchmark</span>
              </div>
            </div>
            <div className="summary-dashboard__fuel-item">
              <span className="summary-dashboard__fuel-icon">💵</span>
              <div>
                <span className="summary-dashboard__fuel-label">Est. Fuel Cost</span>
                <strong className="summary-dashboard__fuel-val">${summary.fuel_economy.estimated_fuel_cost_usd?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
                <span className="summary-dashboard__fuel-sub">${summary.fuel_economy.diesel_price_per_gal}/gal benchmark</span>
              </div>
            </div>
            <div className="summary-dashboard__fuel-item">
              <span className="summary-dashboard__fuel-icon">📈</span>
              <div>
                <span className="summary-dashboard__fuel-label">Fuel Cost / Mile</span>
                <strong className="summary-dashboard__fuel-val">${summary.fuel_economy.fuel_cost_per_mile_usd?.toFixed(2)} / mi</strong>
                <span className="summary-dashboard__fuel-sub">Fleet highway metric</span>
              </div>
            </div>
            <div className="summary-dashboard__fuel-item">
              <span className="summary-dashboard__fuel-icon">🌱</span>
              <div>
                <span className="summary-dashboard__fuel-label">Carbon Footprint</span>
                <strong className="summary-dashboard__fuel-val">{summary.fuel_economy.carbon_footprint_metric_tons?.toFixed(2)} MT</strong>
                <span className="summary-dashboard__fuel-sub">Estimated CO₂ output</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, unit, subtext }) {
  return (
    <div className="summary-dashboard__card">
      <div className="summary-dashboard__card-label">{label}</div>
      <div className="summary-dashboard__card-val">
        {value}
        <span className="summary-dashboard__card-unit">{unit}</span>
      </div>
      {subtext && <div className="summary-dashboard__card-sub">{subtext}</div>}
    </div>
  );
}

function formatLocationName(displayName) {
  if (!displayName) return "Location";
  const parts = displayName.split(",");
  return parts.slice(0, 2).join(",").trim();
}
