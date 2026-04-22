import { requestJson } from "./httpClient";

export async function fetchMonthlyContributionInput(userId) {
  return requestJson(`/virtual-account/monthly-contribution-input?user_id=${encodeURIComponent(userId)}`, {
    timeoutMs: 12000,
    retries: 1,
  });
}

export async function saveMonthlyContributionInput(payload) {
  return requestJson("/virtual-account/monthly-contribution-input", {
    method: "POST",
    body: payload,
    retries: 0,
  });
}
