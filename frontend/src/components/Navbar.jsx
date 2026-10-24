import React from "react";

export default function Navbar({
  hasTripLoaded,
  onOpenHistory,
  onPrintLogs,
  onExportPdf,
  recentTripsCount,
  apiHealthy,
}) {
  return (
    <header className="navbar">
      <div className="navbar__brand">
        <div className="navbar__logo">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="1" y="3" width="15" height="13"></rect>
            <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
            <circle cx="5.5" cy="18.5" r="2.5"></circle>
            <circle cx="18.5" cy="18.5" r="2.5"></circle>
          </svg>
        </div>
        <div>
          <div className="navbar__title">
            HAUL LOG <span className="navbar__badge">ELD 49 CFR § 395</span>
          </div>
          <div className="navbar__subtitle">Commercial Fleet Dispatch &amp; Hours-of-Service Engine</div>
        </div>
      </div>

      <div className="navbar__actions">
        <div className="navbar__status" title="Backend API Connectivity">
          <span className={`navbar__status-dot ${apiHealthy ? "navbar__status-dot--live" : ""}`}></span>
          <span className="navbar__status-text">{apiHealthy ? "Engine Online" : "Connecting..."}</span>
        </div>

        <button
          type="button"
          className="navbar__btn navbar__btn--secondary"
          onClick={onOpenHistory}
          title="View previously planned dispatches"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          Recent Dispatches
          {recentTripsCount > 0 && <span className="navbar__count-pill">{recentTripsCount}</span>}
        </button>

        {hasTripLoaded && (
          <>
            <button
              type="button"
              className="navbar__btn navbar__btn--secondary"
              onClick={onExportPdf}
              title="Download all days as an official Form MCS-59 PDF file"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              Export PDF
            </button>
            <button
              type="button"
              className="navbar__btn navbar__btn--primary"
              onClick={onPrintLogs}
              title="Print official FMCSA Driver Daily Logs"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="6 9 6 2 18 2 18 9"></polyline>
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                <rect x="6" y="14" width="12" height="8"></rect>
              </svg>
              Print Daily Logs
            </button>
          </>
        )}
      </div>
    </header>
  );
}

