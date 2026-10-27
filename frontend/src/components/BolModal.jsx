import React from "react";

export default function BolModal({ isOpen, onClose, bolDocument, metadata }) {
  if (!isOpen || !bolDocument) return null;

  const doc = bolDocument;
  const carrier = doc.carrier || {};
  const shipper = doc.shipper || {};
  const consignee = doc.consignee || {};
  const security = doc.cargo_security || {};
  const lineItems = doc.line_items || [];
  const totals = doc.totals || {};
  const sigs = doc.signatures || {};

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card bol-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Header Bar */}
        <div className="modal-header">
          <div>
            <div className="bol-modal__eyebrow">
              FMCSA 49 CFR § 395.8(d)(17) · Official Shipping Document &amp; Cargo Manifest
            </div>
            <h2 className="modal-title">Uniform Straight Bill of Lading (BOL)</h2>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close Bill of Lading"
          >
            ✕
          </button>
        </div>

        {/* Modal Body / Paperwork Sheet */}
        <div className="modal-body bol-modal__body">
          <div className="bol-document">
            {/* Top Sheet Header */}
            <div className="bol-document__header">
              <div className="bol-document__title-block">
                <span className="bol-document__flag">ORIGINAL — NOT NEGOTIABLE</span>
                <h3 className="bol-document__main-title">UNIFORM STRAIGHT BILL OF LADING</h3>
                <span className="bol-document__statute">{doc.regulatory_statute}</span>
              </div>
              <div className="bol-document__barcode-block">
                <div className="bol-document__barcode-lines" aria-hidden="true">
                  <span></span><span></span><span></span><span></span><span></span>
                  <span></span><span></span><span></span><span></span><span></span>
                  <span></span><span></span><span></span><span></span><span></span>
                  <span></span><span></span><span></span><span></span><span></span>
                </div>
                <strong className="bol-document__bol-num">{doc.bol_number}</strong>
                <span className="bol-document__issue-date">Date Issued: {doc.date_issued_formatted}</span>
              </div>
            </div>

            {/* Carrier & Equipment Banner */}
            <div className="bol-document__carrier-strip">
              <div>
                <span className="bol-field-label">Operating Motor Carrier:</span>
                <strong className="bol-field-val">{carrier.name || metadata?.carrier_name}</strong>
              </div>
              <div>
                <span className="bol-field-label">Driver Name:</span>
                <strong className="bol-field-val">{carrier.driver_name || metadata?.driver_name}</strong>
              </div>
              <div>
                <span className="bol-field-label">Power Unit (Tractor):</span>
                <strong className="bol-field-val">{carrier.tractor_number || metadata?.truck_number}</strong>
              </div>
              <div>
                <span className="bol-field-label">Semi-Trailer Unit:</span>
                <strong className="bol-field-val">{carrier.trailer_number || metadata?.trailer_number}</strong>
              </div>
            </div>

            {/* Shipper & Consignee Facility Address Grid */}
            <div className="bol-document__parties-grid">
              <div className="bol-document__party-card">
                <span className="bol-document__party-role">SHIPPER (ORIGIN FACILITY / PICKUP)</span>
                <h4 className="bol-document__facility-name">{shipper.facility_name}</h4>
                <p className="bol-document__facility-addr">{shipper.address}</p>
                <div className="bol-document__party-meta">
                  <span>Dock Hours: 07:00 – 17:00</span>
                  <span>Freight Terms: Prepaid</span>
                </div>
              </div>

              <div className="bol-document__party-card">
                <span className="bol-document__party-role">CONSIGNEE (DESTINATION / RECEIVER)</span>
                <h4 className="bol-document__facility-name">{consignee.facility_name}</h4>
                <p className="bol-document__facility-addr">{consignee.address}</p>
                <div className="bol-document__party-meta">
                  <span>Receiving Dock: Bay #4</span>
                  <span>Special: Liftgate Required</span>
                </div>
              </div>
            </div>

            {/* Cargo Security & Tamper Seal Badge */}
            <div className="bol-document__seal-box">
              <div className="bol-document__seal-icon">🔒</div>
              <div className="bol-document__seal-info">
                <strong>Cargo Security Seal: {security.seal_number}</strong>
                <span>
                  {security.seal_type} · Tamper-evident seal applied and verified prior to terminal departure.
                </span>
              </div>
              <div className="bol-document__seal-badge">SEAL VERIFIED</div>
            </div>

            {/* Freight Line Items Table */}
            <div className="bol-document__table-wrap">
              <table className="bol-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Qty / Handling Units</th>
                    <th>Commodity &amp; Cargo Description</th>
                    <th>NMFC Class</th>
                    <th style={{ textAlign: "right" }}>Gross Weight (lbs)</th>
                    <th style={{ textAlign: "right" }}>Gross Weight (kg)</th>
                  </tr>
                </thead>
                <tbody>
                  {lineItems.map((item) => (
                    <tr key={item.item_number}>
                      <td style={{ textAlign: "center" }}>#{item.item_number}</td>
                      <td>
                        <strong>{item.quantity}</strong> {item.packaging_type}
                      </td>
                      <td>
                        <span className="bol-table__commodity">{item.commodity_description}</span>
                        <small className="bol-table__subtext">Standard Commercial Freight · Non-Hazardous</small>
                      </td>
                      <td style={{ textAlign: "center" }}>Class {item.nmfc_freight_class}</td>
                      <td style={{ textAlign: "right" }}>
                        <strong>{item.weight_lbs?.toLocaleString()} lbs</strong>
                      </td>
                      <td style={{ textAlign: "right" }}>{item.weight_kg?.toLocaleString()} kg</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan="4" style={{ textAlign: "right", fontWeight: 700 }}>
                      TOTAL FREIGHT SHIPMENT WEIGHT:
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <strong className="bol-table__total-weight">
                        {totals.total_weight_lbs?.toLocaleString()} lbs
                      </strong>
                    </td>
                    <td style={{ textAlign: "right" }}>{totals.total_weight_kg?.toLocaleString()} kg</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Special Instructions & Liability Notice */}
            <div className="bol-document__legal-section">
              <div className="bol-document__instructions">
                <span className="bol-legal-title">Special Handling Instructions:</span>
                <p>{doc.special_instructions}</p>
              </div>
              <div className="bol-document__carmack">
                <span className="bol-legal-title">Uniform Carrier Liability (49 U.S.C. § 14706):</span>
                <p>{doc.legal_liability_terms}</p>
              </div>
            </div>

            {/* Signatures & Certification Block */}
            <div className="bol-document__signatures-grid">
              <div className="bol-sig-card">
                <span className="bol-sig-role">SHIPPER CERTIFICATION</span>
                <div className="bol-sig-line">
                  <span className="bol-sig-name">{sigs.shipper_signature}</span>
                </div>
                <span className="bol-sig-caption">Authorized Shipper Representative</span>
              </div>

              <div className="bol-sig-card">
                <span className="bol-sig-role">CARRIER / DRIVER ACKNOWLEDGEMENT</span>
                <div className="bol-sig-line bol-sig-line--signed">
                  <span className="bol-sig-name">{sigs.driver_signature}</span>
                </div>
                <span className="bol-sig-caption">Professional Property-Carrying Driver</span>
              </div>

              <div className="bol-sig-card">
                <span className="bol-sig-role">CONSIGNEE DELIVERY RECEIPT</span>
                <div className="bol-sig-line bol-sig-line--pending">
                  <span className="bol-sig-name">{sigs.consignee_signature}</span>
                </div>
                <span className="bol-sig-caption">Destination Receiving Manager</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button
            type="button"
            className="navbar__btn navbar__btn--secondary"
            onClick={() => window.print()}
          >
            Print Bill of Lading
          </button>
          <button type="button" className="navbar__btn navbar__btn--primary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
