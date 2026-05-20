// Typed client for the Threat-Lock backend REST API.
import type {
  Alert,
  EventItem,
  Health,
  Status,
  TxResponse,
} from "./types";

export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  opts: { method?: string; body?: unknown; token?: string | null } = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  if (opts.token) headers["Authorization"] = `Bearer ${opts.token}`;

  let res: Response;
  try {
    res = await fetch(`${BACKEND_URL}${path}`, {
      method: opts.method ?? "GET",
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "Cannot reach the backend. Is it running?");
  }

  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    /* empty body */
  }

  if (!res.ok) {
    const detail =
      (data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : undefined) ?? `Request failed (${res.status})`;
    throw new ApiError(res.status, detail);
  }
  return data as T;
}

export const api = {
  health: () => request<Health>("/health"),
  getStatus: () => request<Status>("/contract/status"),
  getEvents: (limit = 25) => request<EventItem[]>(`/contract/events?limit=${limit}`),
  getAlerts: (limit = 50) => request<Alert[]>(`/alerts?limit=${limit}`),

  report: (
    body: { score: number; reason: string; source?: string },
    token?: string | null,
  ) => request<TxResponse>("/contract/report", { method: "POST", body, token }),

  verify: (body: { evidence: string }, token?: string | null) =>
    request<TxResponse>("/contract/verify", { method: "POST", body, token }),

  pause: (body: { reason: string }, token?: string | null) =>
    request<TxResponse>("/contract/pause", { method: "POST", body, token }),

  unpause: (body: { reason: string }, token?: string | null) =>
    request<TxResponse>("/contract/unpause", { method: "POST", body, token }),

  setThreshold: (body: { new_threshold: number }, token?: string | null) =>
    request<TxResponse>("/contract/threshold", { method: "POST", body, token }),
};
