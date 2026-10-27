import React, { useEffect, useState } from "react";
import Navbar from "./components/Navbar.jsx";
import TripForm from "./components/TripForm.jsx";
import SummaryBar from "./components/SummaryBar.jsx";
import RouteMap from "./components/RouteMap.jsx";
import StopsTimeline from "./components/StopsTimeline.jsx";
import DailyLogSheet from "./components/DailyLogSheet.jsx";
import TripHistoryModal from "./components/TripHistoryModal.jsx";
import DvirModal from "./components/DvirModal.jsx";
import BolModal from "./components/BolModal.jsx";
import { checkBackendHealth, downloadTripPdf, fetchRecentTrips, planTrip } from "./api.js";
import "./App.css";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isDvirOpen, setIsDvirOpen] = useState(false);
  const [isBolOpen, setIsBolOpen] = useState(false);
  const [recentTripsCount, setRecentTripsCount] = useState(0);
  const [apiHealthy, setApiHealthy] = useState(true);
  const [selectedDayFilter, setSelectedDayFilter] = useState("all");

  useEffect(() => {
    let timer;
    let isMounted = true;

    async function checkHealthAndLoadTrips() {
      try {
        await checkBackendHealth();
        if (isMounted) {
          setApiHealthy(true);
          try {
            const trips = await fetchRecentTrips();
            if (isMounted) setRecentTripsCount(trips.length);
          } catch {
            // Non-blocking
          }
        }
      } catch {
        if (isMounted) {
          setApiHealthy(false);
          // Auto-retry polling if server is still spinning up on Render free tier
          timer = setTimeout(checkHealthAndLoadTrips, 7000);
        }
      }
    }

    checkHealthAndLoadTrips();

    return () => {
      isMounted = false;
      if (timer) clearTimeout(timer);
    };
  }, []);

  async function handleTripSubmit(formData) {
    setLoading(true);
    setError(null);
    try {
      const data = await planTrip(formData);
      setResult(data);
      setSelectedDayFilter("all");
      // Refresh count
      setRecentTripsCount((c) => c + 1);
    } catch (err) {
      setError(err.message || "Failed to calculate route and logs.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function handleSelectFromHistory(loadedTrip) {
    setResult(loadedTrip);
    setSelectedDayFilter("all");
    setError(null);
  }

  const daysToDisplay = result?.daily_logs
    ? selectedDayFilter === "all"
      ? result.daily_logs
      : result.daily_logs.filter((d) => String(d.day_number) === selectedDayFilter)
    : [];

  return (
    <div className="app-shell">
      <Navbar
        hasTripLoaded={Boolean(result)}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onOpenDvir={() => setIsDvirOpen(true)}
        onOpenBol={() => setIsBolOpen(true)}
        dvirCount={result?.dvir_reports?.length || 0}
        onPrintLogs={() => window.print()}
        onExportPdf={() => downloadTripPdf(result)}
        recentTripsCount={recentTripsCount}
        apiHealthy={apiHealthy}
      />

      <div className="app-container">
        {/* Left Side: Dispatch Form Sidebar */}
        <aside className="app-sidebar no-print">
          <TripForm onSubmit={handleTripSubmit} loading={loading} />
        </aside>

        {/* Right Side: Operational Dashboard & Form MCS-59 Log Sheets */}
        <main className="app-main">
          {/* Empty / Initial State */}
          {!result && !loading && !error && (
            <div className="app-empty">
              <div className="app-empty__icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
                </svg>
              </div>
              <h2 className="app-empty__title">Dispatch System Ready</h2>
              <p className="app-empty__text">
                Specify origin, pickup, and delivery locations on the left to compute the highway corridor,
                simulate FMCSA 49 CFR § 395 Hours-of-Service rules, and generate official Driver Daily Log sheets.
              </p>
              <div className="app-empty__shortcuts">
                <span>Quick Tip:</span> Click any preset freight corridor on the dispatch console for an instant demo.
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="app-loading">
              <div className="app-loading__spinner">◈</div>
              <h3 className="app-loading__title">Computing Logistics Corridor</h3>
              <p className="app-loading__text">
                Resolving geocodes · Querying OSRM road network · Simulating 70h/8-day FMCSA rules · Building 24-hr ELD grids...
              </p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="app-error">
              <div className="app-error__icon">⚠️</div>
              <div className="app-error__content">
                <h3 className="app-error__title">Dispatch Calculation Error</h3>
                <p className="app-error__message">{error}</p>
                <div className="app-error__hint">
                  Please verify that city and state names are spelled correctly (e.g., &quot;Dallas, TX&quot;),
                  ensure pickup and drop-off are distinct locations, and check your internet connection.
                </div>
              </div>
            </div>
          )}

          {/* Result Content */}
          {result && !loading && (
            <div className="app-results">
              <SummaryBar
                route={result.route}
                summary={result.summary}
                locations={result.locations}
                metadata={result.metadata}
                dvirReports={result.dvir_reports}
                onOpenDvir={() => setIsDvirOpen(true)}
                onOpenBol={() => setIsBolOpen(true)}
                bolDocument={result.bol_document}
              />

              <div className="no-print">
                <RouteMap
                  route={result.route}
                  locations={result.locations}
                  stops={result.stops}
                />
              </div>

              <div className="no-print">
                <StopsTimeline stops={result.stops} />
              </div>

              {/* Form MCS-59 ELD Daily Log Sheets Section */}
              <section className="app-logs-section">
                <div className="app-logs-section__header no-print">
                  <div>
                    <h2 className="app-logs-section__title">
                      Official Driver&apos;s Daily Log Sheets (Form MCS-59)
                    </h2>
                    <span className="app-logs-section__subtitle">
                      24-hour midnight-to-midnight status records compliant with 49 CFR § 395.8
                    </span>
                  </div>

                  {/* Day Filter Tabs */}
                  {result.daily_logs.length > 1 && (
                    <div className="app-logs-section__tabs" role="tablist">
                      <button
                        type="button"
                        className={`app-logs-section__tab ${selectedDayFilter === "all" ? "app-logs-section__tab--active" : ""}`}
                        onClick={() => setSelectedDayFilter("all")}
                      >
                        All Days ({result.daily_logs.length})
                      </button>
                      {result.daily_logs.map((d) => (
                        <button
                          key={d.day_number}
                          type="button"
                          className={`app-logs-section__tab ${selectedDayFilter === String(d.day_number) ? "app-logs-section__tab--active" : ""}`}
                          onClick={() => setSelectedDayFilter(String(d.day_number))}
                        >
                          Day {d.day_number}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="app-logs-section__list">
                  {daysToDisplay.map((day, idx) => (
                    <DailyLogSheet
                      key={day.date}
                      day={day}
                      dayIndex={idx}
                      metadata={result.metadata}
                      onDownloadPdf={(dayNum) => downloadTripPdf(result, dayNum)}
                    />
                  ))}
                </div>
              </section>
            </div>
          )}
        </main>
      </div>

      <TripHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onSelectTrip={handleSelectFromHistory}
      />

      <DvirModal
        isOpen={isDvirOpen}
        onClose={() => setIsDvirOpen(false)}
        dvirReports={result?.dvir_reports}
        metadata={result?.metadata}
      />

      <BolModal
        isOpen={isBolOpen}
        onClose={() => setIsBolOpen(false)}
        bolDocument={result?.bol_document}
        metadata={result?.metadata}
      />
    </div>
  );
}
