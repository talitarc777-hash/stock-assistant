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

export async function fetchMonthlyContributions(userId) {
  return requestJson(`/monthly-contributions?user_id=${encodeURIComponent(userId)}`);
}

export async function initializeMonthlyContributions(userId) {
  return requestJson("/monthly-contributions/initialize", {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
}

export async function updateMonthlyContributions(payload) {
  return requestJson("/monthly-contributions/update", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createMonthlyContributions(payload) {
  return requestJson("/monthly-contributions/create", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
