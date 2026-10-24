import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";

const STOP_CATEGORIES = {
  pickup: {
    color: "#ffb627",
    textColor: "#12171e",
    label: "Shipper Pickup",
    badge: "Origin Terminal",
  },
  dropoff: {
    color: "#10b981",
    textColor: "#06281e",
    label: "Receiver Delivery",
    badge: "Destination Terminal",
  },
  fuel: {
    color: "#3b82f6",
    textColor: "#ffffff",
    label: "Fuel & Walk-Around",
    badge: "1,000-Mi Interval",
  },
  rest_break: {
    color: "#f59e0b",
    textColor: "#1f1402",
    label: "30-Min Rest Break",
    badge: "49 CFR § 395.3",
  },
  daily_reset: {
    color: "#8b5cf6",
    textColor: "#ffffff",
    label: "10-Hr Off-Duty Reset",
    badge: "49 CFR § 395.3(a)(1)",
  },
  cycle_restart: {
    color: "#ec4899",
    textColor: "#ffffff",
    label: "34-Hr Cycle Restart",
    badge: "49 CFR § 395.3(d)",
  },
};

/**
 * Ensures the Leaflet map automatically re-fits its viewport whenever
 * the calculated route geometry changes.
 */
function MapBoundsUpdater({ bounds }) {
  const map = useMap();

  useEffect(() => {
    if (bounds && bounds.isValid()) {
      map.fitBounds(bounds, { padding: [48, 48], maxZoom: 14 });
    }
  }, [bounds, map]);

  return null;
}

function createPinIcon(color, text, textColor = "#10151b") {
  return L.divIcon({
    className: "leaflet-custom-pin",
    html: `
      <div style="display:flex;flex-direction:column;align-items:center;transform:translateY(-100%);">
        <div style="background:${color};color:${textColor};font-family:'Oswald',sans-serif;font-weight:700;font-size:11px;padding:3px 8px;border-radius:4px;white-space:nowrap;box-shadow:0 3px 8px rgba(0,0,0,0.5);letter-spacing:0.04em;text-transform:uppercase;border:1px solid rgba(255,255,255,0.2);">
          ${text}
        </div>
        <div style="width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:8px solid ${color};"></div>
      </div>
    `,
    iconSize: [80, 40],
    iconAnchor: [40, 0],
  });
}

function createStopIcon(color, iconSymbol = "•") {
  return L.divIcon({
    className: "leaflet-custom-dot",
    html: `
      <div style="width:20px;height:20px;border-radius:50%;background:${color};border:2px solid #0f151c;box-shadow:0 0 0 3px ${color}55, 0 3px 6px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;color:#0f151c;font-size:10px;font-weight:900;">
        ${iconSymbol}
      </div>
    `,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
}

export default function RouteMap({ route, locations, stops }) {
  const [activeFilter, setActiveFilter] = useState("all");

  if (!route || !route.geometry || route.geometry.length === 0) {
    return null;
  }

  const positions = route.geometry.map(([lat, lon]) => [lat, lon]);
  const bounds = L.latLngBounds(positions);

  const filteredStops = stops.filter((s) => {
    if (activeFilter === "all") return true;
    if (activeFilter === "fuel") return s.type === "fuel";
    if (activeFilter === "rest") return s.type === "rest_break" || s.type === "daily_reset" || s.type === "cycle_restart";
    if (activeFilter === "terminals") return s.type === "pickup" || s.type === "dropoff";
    return true;
  });

  return (
    <div className="route-map-card">
      <div className="route-map-card__header">
        <div className="route-map-card__title-group">
          <h2 className="route-map-card__title">Highway Corridor &amp; Stop Visualizer</h2>
          <span className="route-map-card__subtitle">
            {route.total_distance_miles.toLocaleString()} miles · {stops.length} planned compliance stops
          </span>
        </div>

        {/* Map Filter Controls */}
        <div className="route-map-card__filters" role="group" aria-label="Filter Map Stops">
          <button
            type="button"
            className={`route-map-card__filter-btn ${activeFilter === "all" ? "route-map-card__filter-btn--active" : ""}`}
            onClick={() => setActiveFilter("all")}
          >
            All Stops ({stops.length})
          </button>
          <button
            type="button"
            className={`route-map-card__filter-btn ${activeFilter === "fuel" ? "route-map-card__filter-btn--active" : ""}`}
            onClick={() => setActiveFilter("fuel")}
          >
            Fueling ({stops.filter((s) => s.type === "fuel").length})
          </button>
          <button
            type="button"
            className={`route-map-card__filter-btn ${activeFilter === "rest" ? "route-map-card__filter-btn--active" : ""}`}
            onClick={() => setActiveFilter("rest")}
          >
            Mandatory Rests ({stops.filter((s) => s.type === "rest_break" || s.type === "daily_reset" || s.type === "cycle_restart").length})
          </button>
          <button
            type="button"
            className={`route-map-card__filter-btn ${activeFilter === "terminals" ? "route-map-card__filter-btn--active" : ""}`}
            onClick={() => setActiveFilter("terminals")}
          >
            Terminals
          </button>
        </div>
      </div>

      <div className="route-map-card__viewport">
        <MapContainer
          bounds={bounds}
          boundsOptions={{ padding: [48, 48] }}
          scrollWheelZoom={true}
          className="route-map-card__container"
        >
          <MapBoundsUpdater bounds={bounds} />

          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Polyline Route Corridor */}
          <Polyline
            positions={positions}
            pathOptions={{
              color: "#ffb627",
              weight: 5,
              opacity: 0.95,
              lineJoin: "round",
            }}
          />

          {/* Tractor Origin Pin */}
          {locations.current && (
            <Marker
              position={[locations.current.lat, locations.current.lon]}
              icon={createPinIcon("#94a3b8", "Origin", "#0f172a")}
            >
              <Popup className="route-popup">
                <div className="route-popup__content">
                  <div className="route-popup__badge route-popup__badge--origin">Dispatch Origin</div>
                  <strong className="route-popup__title">Tractor Departure Point</strong>
                  <p className="route-popup__desc">{locations.current.display_name}</p>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Stops & Terminal Waypoints */}
          {filteredStops.map((stop, idx) => {
            if (!stop.position) return null;
            const config = STOP_CATEGORIES[stop.type] || {
              color: "#cbd5e1",
              textColor: "#0f172a",
              label: stop.label,
              badge: "Stop",
            };

            const isTerminal = stop.type === "pickup" || stop.type === "dropoff";
            const icon = isTerminal
              ? createPinIcon(config.color, config.label, config.textColor)
              : createStopIcon(config.color, stop.type === "fuel" ? "⛽" : "⏱");

            return (
              <Marker key={`${stop.type}-${idx}`} position={stop.position} icon={icon}>
                <Popup className="route-popup">
                  <div className="route-popup__content">
                    <div
                      className="route-popup__badge"
                      style={{ backgroundColor: `${config.color}22`, color: config.color, borderColor: config.color }}
                    >
                      {config.badge}
                    </div>
                    <strong className="route-popup__title">{stop.label}</strong>
                    <div className="route-popup__details">
                      <div><strong>Duration:</strong> {stop.duration_hours} hrs</div>
                      <div><strong>Odometer:</strong> Mile {Math.round(stop.cumulative_miles).toLocaleString()}</div>
                      {stop.citation && (
                        <div className="route-popup__citation">Ref: {stop.citation}</div>
                      )}
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
