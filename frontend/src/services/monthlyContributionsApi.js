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

export async function fetchMonthlyContributionInput(userId) {
  return requestJson(
    `/virtual-account/monthly-contribution-input?user_id=${encodeURIComponent(userId)}`
  );
}

export async function saveMonthlyContributionInput(payload) {
  return requestJson("/virtual-account/monthly-contribution-input", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
