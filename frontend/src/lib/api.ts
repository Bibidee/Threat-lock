// Typed client for the Threat-Lock backend API.
import { API_BASE_URL } from "./constants";
import type {
  AdminConfig,
  Health,
  MonitoringRun,
  MonitoringSources,
  SystemStatus,
  ThreatPayload,
  ThreatReport,
  ThreatResult,
  VaultStatus,
} from "@/types";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function req<T>(path: string, opts: { method?: string; body?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: opts.method ?? "GET",
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "Cannot reach the backend API. Is it running?");
  }
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    /* empty */
  }
  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `Request failed (${res.status})`;
    throw new ApiError(res.status, detail);
  }
  return data as T;
}

// ---- reads ----
export const getHealth = () => req<Health>("/api/health");
export const getSystemStatus = () => req<SystemStatus>("/api/system/status");
export const getThreats = (limit = 50) => req<ThreatReport[]>(`/api/threats?limit=${limit}`);
export const getLatestThreat = () => req<ThreatReport | null>("/api/threats/latest");
export const getAdminConfig = () => req<AdminConfig>("/api/admin/config");
export const getMonitoringSources = () => req<MonitoringSources>("/api/monitoring/sources");
export const getMonitoringRuns = (limit = 20) =>
  req<MonitoringRun[]>(`/api/monitoring/runs?limit=${limit}`);

// ---- actions ----
export const runMonitoringScan = () => req<MonitoringRun>("/api/monitoring/run-scan", { method: "POST" });

export const simulateThreat = (payload: ThreatPayload) =>
  req<ThreatResult>("/api/threats/simulate", { method: "POST", body: payload });

export const simulateNormalActivity = () =>
  simulateThreat({
    protocol: "DemoDAO",
    source: "explorer_monitor",
    event_type: "generic",
    description: "Routine governance vote executed.",
    evidence: "Normal governance activity; small balanced transfers; nothing anomalous.",
    amount_usd: 5000,
    tx_count: 4,
    severity_hint: "low",
  });

export const simulateSuspiciousWallet = () =>
  simulateThreat({
    protocol: "DemoDAO",
    source: "explorer_monitor",
    event_type: "suspicious_wallet_interaction",
    description: "Treasury interacted with a freshly-funded wallet.",
    evidence:
      "Treasury sent funds to a 2-hour-old wallet that immediately bridged out; mild anomaly worth review.",
    wallet: "0x000000000000000000000000000000000000dead",
    amount_usd: 180000,
    tx_count: 12,
    severity_hint: "medium",
  });

export const simulateActiveExploit = () =>
  simulateThreat({
    protocol: "DemoDAO",
    source: "explorer_monitor",
    event_type: "treasury_drain",
    description: "Treasury draining via repeated withdrawals.",
    evidence:
      "Treasury wallet drained ~4200 ETH across 3 transactions to a fresh address; repeated withdraw() calls indicating automated exploitation; bridge liquidity emptied.",
    wallet: "0x00000000000000000000000000000000baddbadd",
    amount_usd: 9500000,
    tx_count: 47,
    severity_hint: "critical",
  });

export const manualPause = (payload: { reason: string; wallet: string }) =>
  req<{ paused: boolean; action: string; message: string; tx_hash?: string | null }>(
    "/api/admin/manual-pause",
    { method: "POST", body: payload },
  );

export const unpause = (payload: { recovery_note: string; wallet: string }) =>
  req<{ paused: boolean; action: string; message: string; tx_hash?: string | null }>(
    "/api/admin/unpause",
    { method: "POST", body: payload },
  );

// ---- protected vault ----
export const getVaultStatus = () => req<VaultStatus>("/api/vault/status");
export const vaultDeposit = (amount: number) =>
  req<{ result: string; tx_hash?: string | null }>("/api/vault/deposit", {
    method: "POST",
    body: { amount },
  });
export const vaultWithdraw = (amount: number) =>
  req<{ result: string; tx_hash?: string | null }>("/api/vault/withdraw", {
    method: "POST",
    body: { amount },
  });
