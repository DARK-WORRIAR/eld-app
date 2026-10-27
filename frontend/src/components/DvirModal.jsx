import React, { useState } from "react";

export default function DvirModal({ isOpen, onClose, dvirReports, metadata }) {
  if (!isOpen || !dvirReports || dvirReports.length === 0) return null;

  const [activeReportIdx, setActiveReportIdx] = useState(0);
  const currentReport = dvirReports[activeReportIdx] || dvirReports[0];

  function handlePrint() {
    document.body.classList.add("modal-open-dvir");
    const cleanup = () => {
      document.body.classList.remove("modal-open-dvir");
      window.removeEventListener("afterprint", cleanup);
    };
    window.addEventListener("afterprint", cleanup);
    window.print();
    setTimeout(cleanup, 2500);
  }

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card dvir-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <div className="dvir-modal__eyebrow">
              FMCSA 49 CFR Part 396 · Vehicle Inspection &amp; Maintenance Safety Standard
            </div>
            <h2 className="modal-title">Driver Vehicle Inspection Report (DVIR)</h2>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close DVIR Inspector"
          >
            ✕
          </button>
        </div>

        {/* Inspection Selector Tabs */}
        <div className="dvir-modal__tabs">
          {dvirReports.map((report, idx) => (
            <button
              key={report.report_id}
              type="button"
              className={`dvir-modal__tab ${idx === activeReportIdx ? "dvir-modal__tab--active" : ""}`}
              onClick={() => setActiveReportIdx(idx)}
            >
              <span className="dvir-modal__tab-type">{report.inspection_type}</span>
              <span className="dvir-modal__tab-id">{report.report_id}</span>
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div className="modal-body dvir-modal__body">
          {/* Metadata Grid */}
          <div className="dvir-modal__meta-grid">
            <div className="dvir-modal__meta-item">
              <span className="dvir-modal__meta-label">Motor Carrier:</span>
              <strong className="dvir-modal__meta-val">
                {currentReport.carrier_name || metadata?.carrier_name || "Apex Logistics Freight, Inc."}
              </strong>
            </div>
            <div className="dvir-modal__meta-item">
              <span className="dvir-modal__meta-label">Commercial Vehicle:</span>
              <strong className="dvir-modal__meta-val">
                {currentReport.vehicle_id || metadata?.truck_number || "TRK-409"}
              </strong>
            </div>
            <div className="dvir-modal__meta-item">
              <span className="dvir-modal__meta-label">Inspected By:</span>
              <strong className="dvir-modal__meta-val">
                {currentReport.driver_name || metadata?.driver_name || "Commercial Driver"}
              </strong>
            </div>
            <div className="dvir-modal__meta-item">
              <span className="dvir-modal__meta-label">Inspection Date/Time:</span>
              <strong className="dvir-modal__meta-val">{currentReport.time_formatted}</strong>
            </div>
            <div className="dvir-modal__meta-item">
              <span className="dvir-modal__meta-label">Inspection Location:</span>
              <strong className="dvir-modal__meta-val">{currentReport.location_description}</strong>
            </div>
            <div className="dvir-modal__meta-item">
              <span className="dvir-modal__meta-label">Odometer Reading:</span>
              <strong className="dvir-modal__meta-val">
                {currentReport.odometer_miles?.toLocaleString()} miles
              </strong>
            </div>
          </div>

          {/* Overall Safety Status Callout */}
          <div className="dvir-modal__status-banner">
            <div className="dvir-modal__status-icon">✓</div>
            <div className="dvir-modal__status-info">
              <h3 className="dvir-modal__status-title">
                CONDITION OF VEHICLE SATISFACTORY · SAFE TO OPERATE
              </h3>
              <p className="dvir-modal__status-desc">
                Conducted in accordance with {currentReport.regulatory_citation}. All 12 mandatory commercial
                safety components verified operable. No safety defects or mechanical deficiencies identified.
              </p>
            </div>
            <div className="dvir-modal__status-pill">12 / 12 PASS</div>
          </div>

          {/* 12-Item FMCSA Component Checklist */}
          <div className="dvir-modal__checklist-section">
            <div className="dvir-modal__section-header">
              <h4 className="dvir-modal__section-title">
                FMCSA 12 Mandatory Component Inspection Items (49 CFR § 396.11(a)(1))
              </h4>
              <span className="dvir-modal__section-sub">Standard commercial walk-around audit points</span>
            </div>

            <div className="dvir-modal__components-grid">
              {(currentReport.components || []).map((comp) => (
                <div key={comp.id} className="dvir-modal__comp-card">
                  <div className="dvir-modal__comp-top">
                    <span className="dvir-modal__comp-cat">{comp.category}</span>
                    <span className="dvir-modal__comp-badge">PASS</span>
                  </div>
                  <div className="dvir-modal__comp-name">{comp.name}</div>
                  <div className="dvir-modal__comp-notes">{comp.notes}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Driver Digital Certification Block */}
          <div className="dvir-modal__cert-box">
            <div className="dvir-modal__cert-header">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              </svg>
              <span>Driver Digital Certification &amp; Sign-off</span>
            </div>
            <p className="dvir-modal__cert-statement">
              &quot;{currentReport.driver_certification?.statement}&quot;
            </p>
            <div className="dvir-modal__signature-row">
              <div>
                <span className="dvir-modal__sig-label">Certified Driver:</span>
                <strong className="dvir-modal__sig-val">
                  {currentReport.driver_certification?.certified_by}
                </strong>
              </div>
              <div>
                <span className="dvir-modal__sig-label">Electronic Signature:</span>
                <strong className="dvir-modal__sig-val dvir-modal__sig-val--certified">
                  {currentReport.driver_certification?.signature_status}
                </strong>
              </div>
              <div>
                <span className="dvir-modal__sig-label">Mechanic Sign-off:</span>
                <span className="dvir-modal__sig-val dvir-modal__sig-val--exempt">
                  Exempt (No Deficiencies)
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button
            type="button"
            className="navbar__btn navbar__btn--secondary"
            onClick={handlePrint}
          >
            Print Inspection Report
          </button>
          <button type="button" className="navbar__btn navbar__btn--primary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

