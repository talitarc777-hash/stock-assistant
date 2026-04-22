import { requestJson } from "./httpClient";

export async function fetchModelEvaluationSettings(userId) {
  return requestJson(`/model-evaluation/settings?user_id=${encodeURIComponent(userId)}`, {
    timeoutMs: 12000,
    retries: 1,
  });
}

export async function updateModelEvaluationSettings(payload) {
  return requestJson("/model-evaluation/settings", {
    method: "POST",
    body: payload,
    retries: 0,
  });
}
