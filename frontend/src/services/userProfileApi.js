const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const fallbackMessage = `Request failed with status ${response.status}`;
    let detail = fallbackMessage;
    try {
      const payload = await response.json();
      detail = payload?.detail || fallbackMessage;
    } catch {
      detail = fallbackMessage;
    }
    throw new Error(detail);
  }

  return response.json();
}

export async function fetchUserProfile(userId) {
  return requestJson(`/user-profile?user_id=${encodeURIComponent(userId)}&source=dashboard`);
}

export async function updateUserProfileSettings(payload) {
  return requestJson("/user-profile/settings", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchUserWatchlist(userId) {
  return requestJson(`/user-watchlist?user_id=${encodeURIComponent(userId)}`);
}

export async function addUserWatchlistTicker(payload) {
  return requestJson("/user-watchlist/add", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function removeUserWatchlistTicker(payload) {
  return requestJson("/user-watchlist/remove", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchUserAlertSettings(userId) {
  return requestJson(`/user-alert-settings?user_id=${encodeURIComponent(userId)}`);
}

export async function fetchUserAlertScan(userId) {
  return requestJson(`/user-alerts/scan?user_id=${encodeURIComponent(userId)}`);
}

export async function updateUserAlertSettings(payload) {
  return requestJson("/user-alert-settings/update", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
