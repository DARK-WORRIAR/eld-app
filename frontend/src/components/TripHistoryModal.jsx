import React, { useEffect, useState } from "react";
import { fetchRecentTrips, fetchTripDetail } from "../api";

export default function TripHistoryModal({ isOpen, onClose, onSelectTrip }) {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadTrips();
    }
  }, [isOpen]);

  async function loadTrips() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecentTrips();
      setTrips(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelect(tripId) {
    setLoading(true);
    try {
      const fullTrip = await fetchTripDetail(tripId);
      onSelectTrip(fullTrip);
      onClose();
    } catch (err) {
      setError(`Failed to load trip: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-panel__header">
          <div>
            <h2 className="modal-panel__title">Recent Dispatches</h2>
            <p className="modal-panel__subtitle">
              Previously computed routes and ELD compliance log records.
            </p>
          </div>
          <button type="button" className="modal-panel__close" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        <div className="modal-panel__body">
          {loading && (
            <div className="modal-panel__loading">
              <span className="modal-panel__spinner">◈</span> Loading dispatches...
            </div>
          )}

          {error && <div className="modal-panel__error">{error}</div>}

          {!loading && !error && trips.length === 0 && (
            <div className="modal-panel__empty">
              <p>No dispatches recorded yet. Plan a trip on the dispatch sheet to save it here.</p>
            </div>
          )}

          {!loading && trips.length > 0 && (
            <div className="modal-panel__list">
              {trips.map((trip) => (
                <div
                  key={trip.id}
                  className="modal-panel__item"
                  onClick={() => handleSelect(trip.id)}
                  tabIndex={0}
                  role="button"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") handleSelect(trip.id);
                  }}
                >
                  <div className="modal-panel__item-main">
                    <div className="modal-panel__item-route">
                      <span className="modal-panel__point">{trip.pickup_location}</span>
                      <span className="modal-panel__arrow">→</span>
                      <span className="modal-panel__point">{trip.dropoff_location}</span>
                    </div>
                    <div className="modal-panel__item-meta">
                      <span>Origin: {trip.current_location}</span>
                      <span>·</span>
                      <span>Driver: {trip.driver_name || "Commercial Driver"}</span>
                      <span>·</span>
                      <span>Cycle Used: {trip.current_cycle_used_hrs}h</span>
                    </div>
                  </div>
                  <div className="modal-panel__item-right">
                    <span className="modal-panel__badge">
                      {trip.total_distance_miles ? `${trip.total_distance_miles.toLocaleString()} mi` : "Loaded"}
                    </span>
                    <span className="modal-panel__date">
                      {new Date(trip.created_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

