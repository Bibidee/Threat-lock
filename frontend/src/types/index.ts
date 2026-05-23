// Types mirroring the backend API.

export interface Health {
  ok: boolean;
  service: string;
  genlayer_mode: string;
  firebase_backend: string;
}

export interface SystemStatus {
  paused: boolean;
  risk_level: string;
  latest_verdict: string;
  latest_threat_id: string | null;
  latest_score: number;
  latest_reasoning: string;
  last_action: string;
  updated_at: string;
}

export interface ThreatReport {
  id: string;
  protocol: string;
  source: string;
  event_type: string;
  description: string;
  evidence: string;
  wallet?: string | null;
  amount_usd?: number;
  tx_count?: number;
  severity_hint: string;
  local_score: number;
  risk_level: string;
  genlayer_required: boolean;
  genlayer_verdict: string;
  genlayer_score?: number | null;
  genlayer_reasoning?: string | null;
  genlayer_recommended_action?: string | null;
  pause_triggered: boolean;
  status: string;
  source_url?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ThreatResult {
  report_id: string;
  score: number;
  risk_level: string;
  genlayer_required: boolean;
  genlayer_verdict: string;
  genlayer_score?: number | null;
  genlayer_reasoning?: string | null;
  genlayer_recommended_action?: string | null;
  pause_triggered: boolean;
  action: string;
  tx_hash?: string | null;
}

export interface MonitoringSources {
  explorer: {
    enabled: boolean;
    provider: string;
    watched_address: string | null;
    chain: string | null;
  };
  news: { enabled: boolean; source_count: number };
  security_keywords: string[];
}

export interface MonitoringRun {
  id: string;
  started_at: string;
  completed_at: string | null;
  sources_checked: string[];
  signals_found: number;
  threats_ingested: number;
  errors: string[];
  status: string;
}

export interface AdminConfig {
  admin_wallet_address: string;
  genlayer_contract_address: string;
  genlayer_mode: string;
  can_pause: boolean;
  can_unpause: boolean;
}

export interface VaultStatus {
  configured: boolean;
  frozen: boolean;
  freeze_reason: string;
  total_locked: number;
  address: string | null;
}

export interface ThreatPayload {
  protocol?: string;
  source?: string;
  event_type?: string;
  description?: string;
  evidence: string;
  wallet?: string | null;
  amount_usd?: number;
  tx_count?: number;
  severity_hint?: string;
  source_url?: string | null;
  metadata?: Record<string, unknown>;
}
