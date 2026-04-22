const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const RETRYABLE_STATUS_CODES = new Set([408, 429, 500, 502, 503, 504]);

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function parseErrorMessage(response, payloadDetail, fallbackMessage) {
  if (payloadDetail) return String(payloadDetail);
  if (response.status === 503 || response.status === 502 || response.status === 504) {
    return "Server is starting or temporarily busy. Please retry in a moment.";
  }
  if (response.status === 429) {
    return "Server is handling too many requests. Please retry shortly.";
  }
  return fallbackMessage;
}

export async function requestJson(path, options = {}) {
  const {
    method = "GET",
    body,
    headers = {},
    timeoutMs = 12000,
    retries = method === "GET" ? 1 : 0,
    retryDelayMs = 350,
    signal: externalSignal = null,
  } = options;
  const url = `${API_BASE_URL}${path}`;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort("timeout"), timeoutMs);
    let shouldRetry = false;
    try {
      if (externalSignal) {
        if (externalSignal.aborted) {
          throw new Error("Request canceled.");
        }
        externalSignal.addEventListener("abort", () => controller.abort("external_abort"), { once: true });
      }
      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });
      if (!response.ok) {
        const fallbackMessage = `Request failed with status ${response.status}`;
        let detail = "";
        try {
          const payload = await response.json();
          detail = payload?.detail || "";
        } catch {
          detail = "";
        }
        const message = parseErrorMessage(response, detail, fallbackMessage);
        shouldRetry = method === "GET" && RETRYABLE_STATUS_CODES.has(response.status) && attempt < retries;
        if (!shouldRetry) {
          throw new Error(message);
        }
      } else {
        return response.json();
      }
    } catch (error) {
      const abortedByTimeout = error?.name === "AbortError" || String(error?.message || "").includes("timeout");
      shouldRetry = method === "GET" && attempt < retries;
      if (!shouldRetry) {
        if (abortedByTimeout) {
          throw new Error("Server response timed out. The server may be busy, please retry.");
        }
        if (
          error instanceof TypeError ||
          String(error?.message || "").toLowerCase().includes("failed to fetch")
        ) {
          throw new Error("Unable to reach backend API. Server may be restarting or unavailable.");
        }
        throw error;
      }
    } finally {
      window.clearTimeout(timeoutId);
    }
    await sleep(retryDelayMs * (attempt + 1));
  }

  throw new Error("Request failed. Please retry.");
}

