/**
 * API client module for ELD Trip Planner and Compliance Engine.
 * Provides resilient HTTP communication with the Django REST backend.
 */

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");

const DEFAULT_TIMEOUT_MS = 60000;

/**
 * Executes an HTTP fetch with an automated timeout abort signal.
 *
 * @param {string} url - Target URL.
 * @param {RequestInit} [options={}] - Fetch configuration options.
 * @param {number} [timeoutMs=DEFAULT_TIMEOUT_MS] - Timeout threshold in milliseconds.
 * @returns {Promise<Response>}
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(
        "Request timed out waiting for route calculation. If the server was idle (Render free tier), it can take 30–50s to spin up. Please try again in a few seconds."
      );
    }
    throw new Error(
      `Unable to reach the logistics API at ${API_BASE_URL}. If the backend was idle, Render free tier takes ~30–45 seconds to wake up on the first request. Please wait a moment and click Plan Route again.`
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Parses and extracts structured error details from an HTTP error response.
 *
 * @param {Response} response
 * @returns {Promise<string>}
 */
async function parseErrorResponse(response) {
  try {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const data = await response.json();
      if (data.details) {
        if (typeof data.details === "string") return data.details;
        if (typeof data.details === "object") {
          return Object.entries(data.details)
            .map(([field, errs]) => `${field}: ${Array.isArray(errs) ? errs.join(", ") : errs}`)
            .join(" | ");
        }
      }
      return data.error || `Server responded with status ${response.status}.`;
    }
    const text = await response.text();
    return text.slice(0, 160) || `Request failed with HTTP status ${response.status}.`;
  } catch {
    return `Server returned status code ${response.status}.`;
  }
}

/**
 * Plans a commercial freight haul with FMCSA HOS compliance and daily logs.
 *
 * @param {Object} payload - Dispatch parameters.
 * @param {string} payload.current_location - Origin / tractor location.
 * @param {string} payload.pickup_location - Shipper loading facility.
 * @param {string} payload.dropoff_location - Receiver delivery destination.
 * @param {number} payload.current_cycle_used_hrs - Cumulative duty hours logged (0-70).
 * @param {string} [payload.start_time] - ISO-8601 departure timestamp.
 * @param {string} [payload.driver_name] - Primary commercial driver name.
 * @param {string} [payload.carrier_name] - Operating motor carrier name.
 * @param {string} [payload.truck_number] - Power unit identifier.
 * @returns {Promise<Object>} Calculated trip plan, geometry, and daily logs.
 */
export async function planTrip(payload) {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/plan-trip/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await parseErrorResponse(response);
    throw new Error(message);
  }

  return response.json();
}

/**
 * Retrieves the list of recent dispatches stored in the backend database.
 *
 * @returns {Promise<Array<Object>>}
 */
export async function fetchRecentTrips() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/trips/`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    const message = await parseErrorResponse(response);
    throw new Error(message);
  }

  return response.json();
}

/**
 * Retrieves the full compliance payload for a previously saved trip.
 *
 * @param {number|string} tripId - Database primary key of the trip.
 * @returns {Promise<Object>}
 */
export async function fetchTripDetail(tripId) {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/trips/${tripId}/`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    const message = await parseErrorResponse(response);
    throw new Error(message);
  }

  return response.json();
}

/**
 * Checks backend health and database operational status.
 *
 * @returns {Promise<Object>}
 */
export async function checkBackendHealth() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/health/`, {
    method: "GET",
    headers: { Accept: "application/json" },
  }, 20000);

  return response.json();
}

/**
 * Downloads official DOT Form MCS-59 Driver's Daily Log as a PDF file.
 *
 * @param {Object} tripData - Full trip payload.
 * @param {number|null} [dayNumber=null] - Specific day or null for all days.
 */
export async function downloadTripPdf(tripData, dayNumber = null) {
  const queryParam = dayNumber ? `?day=${dayNumber}` : "";
  let response;

  if (tripData?.trip_id) {
    response = await fetchWithTimeout(
      `${API_BASE_URL}/api/trips/${tripData.trip_id}/pdf/${queryParam}`,
      { method: "GET" }
    );
  } else {
    response = await fetchWithTimeout(
      `${API_BASE_URL}/api/export-pdf/${queryParam}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tripData),
      }
    );
  }

  if (!response.ok) {
    const errorMsg = await parseErrorResponse(response);
    throw new Error(errorMsg);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  const daySuffix = dayNumber ? `_Day_${dayNumber}` : "";
  anchor.download = `DOT_Form_MCS59_Log${daySuffix}.pdf`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}
