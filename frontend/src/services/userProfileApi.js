import { requestJson } from "./httpClient";

export async function fetchUserProfile(userId) {
  return requestJson(`/user-profile?user_id=${encodeURIComponent(userId)}&source=dashboard`, {
    timeoutMs: 12000,
    retries: 1,
  });
}

export async function updateUserProfileSettings(payload) {
  return requestJson("/user-profile/settings", {
    method: "POST",
    body: payload,
    retries: 0,
  });
}

export async function fetchUserWatchlist(userId) {
  return requestJson(`/user-watchlist?user_id=${encodeURIComponent(userId)}`, {
    timeoutMs: 12000,
    retries: 1,
  });
}

export async function addUserWatchlistTicker(payload) {
  return requestJson("/user-watchlist/add", {
    method: "POST",
    body: payload,
    retries: 0,
  });
}

export async function removeUserWatchlistTicker(payload) {
  return requestJson("/user-watchlist/remove", {
    method: "POST",
    body: payload,
    retries: 0,
  });
}

export async function fetchUserAlertSettings(userId) {
  return requestJson(`/user-alert-settings?user_id=${encodeURIComponent(userId)}`, {
    timeoutMs: 12000,
    retries: 1,
  });
}

export async function fetchUserAlertScan(userId) {
  return requestJson(`/user-alerts/scan?user_id=${encodeURIComponent(userId)}`, {
    timeoutMs: 14000,
    retries: 1,
  });
}

export async function updateUserAlertSettings(payload) {
  return requestJson("/user-alert-settings/update", {
    method: "POST",
    body: payload,
    retries: 0,
  });
}
