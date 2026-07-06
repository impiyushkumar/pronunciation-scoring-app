// -----------------------------------------------------------------------
// Backend API client
// -----------------------------------------------------------------------

import { AnalysisResponse, ErrorResponse, HealthResponse } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Timeout for the full analyze request (accounts for cold starts + Whisper inference) */
const ANALYZE_TIMEOUT_MS = 180_000; // 3 minutes

/** Timeout for health check */
const HEALTH_TIMEOUT_MS = 10_000; // 10 seconds

/**
 * Send audio file to the backend for pronunciation analysis.
 * Returns the analysis result or throws an error with a user-friendly message.
 */
export async function analyzeAudio(
  file: File,
  signal?: AbortSignal
): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ANALYZE_TIMEOUT_MS);

  // Combine external signal with our timeout signal
  const combinedSignal = signal
    ? combineAbortSignals(signal, controller.signal)
    : controller.signal;

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: "POST",
      body: formData,
      signal: combinedSignal,
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      const errorData = errorBody as ErrorResponse | null;

      if (response.status === 429) {
        throw new ApiError(
          "Too many requests. Please wait a moment and try again.",
          "rate_limited"
        );
      }

      throw new ApiError(
        errorData?.message || `Server error (${response.status}). Please try again.`,
        errorData?.error || "server_error"
      );
    }

    return (await response.json()) as AnalysisResponse;
  } catch (error) {
    clearTimeout(timeout);

    if (error instanceof ApiError) throw error;

    if (error instanceof DOMException && error.name === "AbortError") {
      if (signal?.aborted) {
        throw new ApiError("Upload cancelled.", "cancelled");
      }
      throw new ApiError(
        "Request timed out. The server may be warming up — please try again.",
        "timeout"
      );
    }

    throw new ApiError(
      "Could not connect to the server. Please check your connection and try again.",
      "network_error"
    );
  }
}

/**
 * Ping the backend health endpoint — used to detect cold starts.
 */
export async function checkHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });
    if (!response.ok) return null;
    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

/**
 * Custom error class with machine-readable code for the UI to branch on.
 */
export class ApiError extends Error {
  code: string;
  constructor(message: string, code: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}

/**
 * Combine two AbortSignals — aborts when either fires.
 */
function combineAbortSignals(...signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();
  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort(signal.reason);
      return controller.signal;
    }
    signal.addEventListener("abort", () => controller.abort(signal.reason), {
      once: true,
    });
  }
  return controller.signal;
}
