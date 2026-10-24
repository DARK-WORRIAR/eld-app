import React from "react";

const STOP_BADGES = {
  pickup: { label: "Shipper Loading", color: "var(--amber)", bg: "rgba(255,182,39,0.12)" },
  dropoff: { label: "Receiver Unloading", color: "var(--emerald)", bg: "rgba(16,185,129,0.12)" },
  fuel: { label: "Fueling & Inspection", color: "var(--blue)", bg: "rgba(59,130,246,0.12)" },
  rest_break: { label: "30-Min Rest Break", color: "var(--amber-dim)", bg: "rgba(245,158,11,0.12)" },
  daily_reset: { label: "10-Hr Daily Reset", color: "var(--purple)", bg: "rgba(139,92,246,0.12)" },
  cycle_restart: { label: "34-Hr Cycle Restart", color: "var(--pink)", bg: "rgba(236,72,153,0.12)" },
};

export default function StopsTimeline({ stops }) {
  if (!stops || stops.length === 0) return null;

  return (
    <div className="stops-timeline-card">
      <div className="stops-timeline-card__header">
        <div>
          <h2 className="stops-timeline-card__title">Stops, Fueling &amp; Compliance Schedule</h2>
          <span className="stops-timeline-card__subtitle">
            Chronological sequence of all required non-driving rest, inspection, and terminal events
          </span>
        </div>
        <span className="stops-timeline-card__count">{stops.length} Planned Events</span>
      </div>

      <div className="stops-timeline-card__scroll">
        <div className="stops-timeline-card__track">
          {stops.map((stop, index) => {
            const badge = STOP_BADGES[stop.type] || {
              label: stop.label,
              color: "var(--text-dim)",
              bg: "rgba(255,255,255,0.06)",
            };

            return (
              <div key={index} className="stops-timeline-card__item">
                <div className="stops-timeline-card__item-header">
                  <span className="stops-timeline-card__num">#{index + 1}</span>
                  <span
                    className="stops-timeline-card__badge"
                    style={{ color: badge.color, backgroundColor: badge.bg, borderColor: badge.color }}
                  >
                    {badge.label}
                  </span>
                </div>

                <div className="stops-timeline-card__item-title">{stop.label}</div>

                <div className="stops-timeline-card__metrics">
                  <div>
                    <span className="stops-timeline-card__metric-label">Duration:</span>
                    <strong className="stops-timeline-card__metric-val">{stop.duration_hours} hrs</strong>
                  </div>
                  <div>
                    <span className="stops-timeline-card__metric-label">Odometer:</span>
                    <strong className="stops-timeline-card__metric-val">
                      Mile {Math.round(stop.cumulative_miles).toLocaleString()}
                    </strong>
                  </div>
                </div>

                {stop.start_time_formatted && (
                  <div className="stops-timeline-card__times">
                    {stop.start_time_formatted} → {stop.end_time_formatted}
                  </div>
                )}

                {stop.citation && (
                  <div className="stops-timeline-card__citation">{stop.citation}</div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
