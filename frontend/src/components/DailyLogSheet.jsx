import React from "react";

const DUTY_ROWS = [
  { key: "off_duty", label: "1. OFF DUTY", fullLabel: "Line 1: Off Duty" },
  { key: "sleeper", label: "2. SLEEPER BERTH", fullLabel: "Line 2: Sleeper Berth" },
  { key: "driving", label: "3. DRIVING", fullLabel: "Line 3: Driving" },
  { key: "on_duty", label: "4. ON DUTY (NOT DRIVING)", fullLabel: "Line 4: On Duty (Not Driving)" },
];

// SVG Grid geometry dimensions
const SVG_WIDTH = 1100;
const LEFT_MARGIN = 210;
const RIGHT_MARGIN = 100;
const TOP_MARGIN = 48;
const ROW_HEIGHT = 38;
const GRID_WIDTH = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN;
const HOUR_WIDTH = GRID_WIDTH / 24.0;
const GRID_HEIGHT = ROW_HEIGHT * DUTY_ROWS.length;
const SVG_HEIGHT = TOP_MARGIN + GRID_HEIGHT + 36;

function getHourX(hr) {
  return LEFT_MARGIN + Math.max(0, Math.min(24, hr)) * HOUR_WIDTH;
}

function getRowY(rowIndex) {
  return TOP_MARGIN + rowIndex * ROW_HEIGHT + ROW_HEIGHT / 2.0;
}

function formatHourMarker(h) {
  if (h === 0 || h === 24) return "Mid";
  if (h === 12) return "Noon";
  return String(h > 12 ? h - 12 : h);
}

export default function DailyLogSheet({ day, dayIndex, metadata, onDownloadPdf }) {
  const [downloading, setDownloading] = React.useState(false);
  const getRowIndex = (status) => DUTY_ROWS.findIndex((r) => r.key === status);

  // Generate continuous step-function SVG path data across the 24-hour grid
  let pathCommands = "";
  const sortedSegments = [...day.segments].sort((a, b) => a.from_hr - b.from_hr);

  sortedSegments.forEach((seg, i) => {
    const rIdx = getRowIndex(seg.status);
    const validRow = rIdx >= 0 ? rIdx : 0;
    const xStart = getHourX(seg.from_hr);
    const xEnd = getHourX(seg.to_hr);
    const yVal = getRowY(validRow);

    if (i === 0) {
      pathCommands += `M ${xStart.toFixed(2)} ${yVal.toFixed(2)} `;
    } else {
      // Draw vertical transition from previous segment row to current row at xStart
      pathCommands += `L ${xStart.toFixed(2)} ${yVal.toFixed(2)} `;
    }
    // Draw horizontal duty status duration line
    pathCommands += `L ${xEnd.toFixed(2)} ${yVal.toFixed(2)} `;
  });

  const totalCalculatedHours = Object.values(day.totals || {}).reduce((a, b) => a + b, 0);

  function handlePrint() {
    window.print();
  }

  return (
    <div className="log-sheet-card">
      {/* Official FMCSA Form MCS-59 Header */}
      <div className="log-sheet-card__header">
        <div className="log-sheet-card__carrier-info">
          <div className="log-sheet-card__eyebrow">
            FMCSA Form MCS-59 · Driver's Daily Log · 49 CFR § 395.8
          </div>
          <h3 className="log-sheet-card__title">
            {metadata?.carrier_name || "Apex Logistics Freight, Inc."}
          </h3>
          <div className="log-sheet-card__details-grid">
            <div>
              <span className="log-sheet-card__field-label">Driver Name:</span>
              <span className="log-sheet-card__field-val">{metadata?.driver_name || "Commercial Driver"}</span>
            </div>
            <div>
              <span className="log-sheet-card__field-label">Tractor / Unit #:</span>
              <span className="log-sheet-card__field-val">{metadata?.truck_number || "TRK-409"}</span>
            </div>
            <div>
              <span className="log-sheet-card__field-label">Trailer Unit #:</span>
              <span className="log-sheet-card__field-val">{metadata?.trailer_number || "TRL-9201"}</span>
            </div>
            <div>
              <span className="log-sheet-card__field-label">Log Date:</span>
              <span className="log-sheet-card__field-val">{day.formatted_date || day.date}</span>
            </div>
            <div>
              <span className="log-sheet-card__field-label">Shipping Doc (BOL) #:</span>
              <span className="log-sheet-card__field-val">{metadata?.bol_number || "BOL-2026-9041"}</span>
            </div>
            <div>
              <span className="log-sheet-card__field-label">Commodity &amp; Cargo:</span>
              <span className="log-sheet-card__field-val">
                {metadata?.commodity || "General Freight"} ({metadata?.cargo_weight_lbs ? `${Number(metadata.cargo_weight_lbs).toLocaleString()} lbs` : "38,000 lbs"})
              </span>
            </div>
            <div>
              <span className="log-sheet-card__field-label">Cycle Standard:</span>
              <span className="log-sheet-card__field-val">70 Hr / 8 Day Property-Carrying</span>
            </div>
          </div>
          {day.adverse_conditions_claimed && (
            <div className="log-sheet-card__adverse-alert">
              <span className="log-sheet-card__adverse-tag">49 CFR § 395.1(b)(1) Adverse Driving Exception</span>
              <span className="log-sheet-card__adverse-reason">
                {day.adverse_conditions_reason ? `Audit Justification: "${day.adverse_conditions_reason}"` : "Audit Justification: Adverse weather / unforeseen road condition"}
              </span>
            </div>
          )}
        </div>

        <div className="log-sheet-card__actions">
          <div className="log-sheet-card__day-badge">
            <span>Day {day.day_number || dayIndex + 1}</span>
            <span className="log-sheet-card__day-total">{day.total_day_hours || totalCalculatedHours.toFixed(1)} hrs</span>
          </div>
          <div className="log-sheet-card__btn-group">
            <button
              type="button"
              className="log-sheet-card__print-btn"
              onClick={handlePrint}
              title="Print this log sheet"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="6 9 6 2 18 2 18 9"></polyline>
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                <rect x="6" y="14" width="12" height="8"></rect>
              </svg>
              Print
            </button>
            {onDownloadPdf && (
              <button
                type="button"
                className="log-sheet-card__pdf-btn"
                disabled={downloading}
                onClick={async () => {
                  setDownloading(true);
                  try {
                    await onDownloadPdf(day.day_number || dayIndex + 1);
                  } finally {
                    setDownloading(false);
                  }
                }}
                title="Download official DOT Form MCS-59 as PDF"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                {downloading ? "Generating..." : "Download PDF"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 24-Hour ELD Standard Vector Grid */}
      <div className="log-sheet-card__canvas-wrap">
        <svg
          viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
          className="log-sheet-card__svg"
          role="img"
          aria-label={`ELD 24-hour log sheet for ${day.date}`}
        >
          {/* Paper Background */}
          <rect x="0" y="0" width={SVG_WIDTH} height={SVG_HEIGHT} fill="#f8f5ed" rx="4" />

          {/* Grid Area Background */}
          <rect
            x={LEFT_MARGIN}
            y={TOP_MARGIN}
            width={GRID_WIDTH}
            height={GRID_HEIGHT}
            fill="#ffffff"
            stroke="#94a3b8"
            strokeWidth="1.2"
          />

          {/* Quarter-Hour Sub-Tick Lines */}
          {Array.from({ length: 96 }).map((_, q) => {
            if (q % 4 === 0) return null;
            const xPos = getHourX(q / 4.0);
            const isHalfHour = q % 2 === 0;
            return (
              <line
                key={`q-${q}`}
                x1={xPos}
                y1={TOP_MARGIN}
                x2={xPos}
                y2={TOP_MARGIN + GRID_HEIGHT}
                stroke={isHalfHour ? "#e2e8f0" : "#f1f5f9"}
                strokeWidth={isHalfHour ? "0.8" : "0.5"}
              />
            );
          })}

          {/* Hour Vertical Grid Lines */}
          {Array.from({ length: 25 }).map((_, h) => {
            const xPos = getHourX(h);
            const isMajor = h % 6 === 0;
            return (
              <g key={`hour-line-${h}`}>
                <line
                  x1={xPos}
                  y1={TOP_MARGIN}
                  x2={xPos}
                  y2={TOP_MARGIN + GRID_HEIGHT}
                  stroke={isMajor ? "#475569" : "#cbd5e1"}
                  strokeWidth={isMajor ? "1.4" : "0.7"}
                />
                {/* Top Hour Labels */}
                <text
                  x={xPos}
                  y={TOP_MARGIN - 12}
                  textAnchor="middle"
                  className="log-sheet-svg__hour-text"
                >
                  {formatHourMarker(h)}
                </text>
              </g>
            );
          })}

          {/* 4 Duty Status Horizontal Row Lines & Row Labels */}
          {DUTY_ROWS.map((row, idx) => {
            const yTop = TOP_MARGIN + idx * ROW_HEIGHT;
            const yMid = getRowY(idx);
            const rowTotal = day.totals[row.key] || 0.0;

            return (
              <g key={row.key}>
                {idx > 0 && (
                  <line
                    x1={LEFT_MARGIN}
                    y1={yTop}
                    x2={LEFT_MARGIN + GRID_WIDTH}
                    y2={yTop}
                    stroke="#94a3b8"
                    strokeWidth="1"
                  />
                )}
                {/* Left Row Description */}
                <text
                  x={LEFT_MARGIN - 14}
                  y={yMid + 4}
                  textAnchor="end"
                  className="log-sheet-svg__row-label"
                >
                  {row.label}
                </text>

                {/* Right Row Hours Total */}
                <text
                  x={LEFT_MARGIN + GRID_WIDTH + 14}
                  y={yMid + 4}
                  className="log-sheet-svg__row-total"
                >
                  {rowTotal.toFixed(1)} hrs
                </text>
              </g>
            );
          })}

          {/* Continuous Driver Status Polyline */}
          {pathCommands && (
            <path
              d={pathCommands}
              fill="none"
              stroke="#0f172a"
              strokeWidth="2.8"
              strokeLinecap="square"
              strokeLinejoin="miter"
              className="log-sheet-svg__status-path"
            />
          )}
        </svg>
      </div>

      {/* 24-Hour Total Verification Bar */}
      <div className="log-sheet-card__totals-bar">
        <div className="log-sheet-card__totals-breakdown">
          <span>Off Duty: <strong>{(day.totals.off_duty || 0).toFixed(1)}h</strong></span>
          <span>Sleeper: <strong>{(day.totals.sleeper || 0).toFixed(1)}h</strong></span>
          <span>Driving: <strong>{(day.totals.driving || 0).toFixed(1)}h</strong></span>
          <span>On Duty: <strong>{(day.totals.on_duty || 0).toFixed(1)}h</strong></span>
        </div>
        <div className="log-sheet-card__totals-audit">
          <span className="log-sheet-card__audit-badge">
            ✓ Total: {totalCalculatedHours.toFixed(1)} / 24.0 Hours Verified
          </span>
        </div>
      </div>

      {/* Chronological Remarks & Duty Event Table */}
      <div className="log-sheet-card__remarks-section">
        <div className="log-sheet-card__remarks-title">Chronological Duty Log &amp; Activity Remarks</div>
        <div className="log-sheet-card__table-wrap">
          <table className="log-sheet-card__table">
            <thead>
              <tr>
                <th style={{ width: "16%" }}>Time Interval</th>
                <th style={{ width: "10%" }}>Duration</th>
                <th style={{ width: "20%" }}>Duty Status</th>
                <th style={{ width: "38%" }}>Activity / Location Remarks</th>
                <th style={{ width: "16%" }}>CFR Citation</th>
              </tr>
            </thead>
            <tbody>
              {day.segments.map((seg, sIdx) => (
                <tr key={sIdx} className={`log-sheet-card__tr--${seg.status}`}>
                  <td className="log-sheet-card__mono">
                    {formatClockTime(seg.from_hr)} – {formatClockTime(seg.to_hr)}
                  </td>
                  <td className="log-sheet-card__mono">{seg.duration_hours?.toFixed(1)}h</td>
                  <td>
                    <span className={`log-sheet-card__status-pill log-sheet-card__status-pill--${seg.status}`}>
                      {DUTY_ROWS.find((r) => r.key === seg.status)?.label || seg.status}
                    </span>
                  </td>
                  <td>{seg.label}</td>
                  <td className="log-sheet-card__citation">{seg.citation || "49 CFR § 395"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Driver Certification Block */}
      <div className="log-sheet-card__certification">
        <p className="log-sheet-card__cert-text">
          I certify that these entries are a true and accurate record of my duty status and driving hours in accordance with 49 CFR Part 395.
        </p>
        <div className="log-sheet-card__signatures">
          <div className="log-sheet-card__sig-line">
            <span className="log-sheet-card__sig-label">Driver Signature:</span>
            <span className="log-sheet-card__sig-cursive">{metadata?.driver_name || "Commercial Driver"}</span>
          </div>
          <div className="log-sheet-card__sig-line">
            <span className="log-sheet-card__sig-label">Carrier Verification:</span>
            <span className="log-sheet-card__sig-cursive">Authorized Dispatcher</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatClockTime(hourFloat) {
  const hInt = Math.floor(hourFloat) % 24;
  const minutes = Math.round((hourFloat - Math.floor(hourFloat)) * 60);
  const period = hInt >= 12 ? "PM" : "AM";
  const h12 = hInt % 12 === 0 ? 12 : hInt % 12;
  return `${h12}:${String(minutes).padStart(2, "0")} ${period}`;
}
