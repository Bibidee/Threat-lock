// Types mirroring the backend API (see backend/app/models/schemas.py).

export interface Status {
  paused: boolean;
  threat_score: number;
  pause_threshold: number;
  event_count: number;
  last_reason: string;
  owner: string;
}

export interface EventItem {
  kind: string;
  score: number;
  reason: string;
  actor: string;
  timestamp: number;
}

export interface Alert {
  id?: string;
  kind?: string;
  severity?: string;
  score?: number | null;
  reason?: string;
  source?: string;
  tx_hash?: string | null;
  created_at?: number;
}

export interface Health {
  status: string;
  env: string;
  genlayer_network: string;
  contract_configured: boolean;
  write_enabled: boolean;
  firebase_enabled: boolean;
  operator_address: string | null;
}

export interface TxResponse {
  tx_hash: string;
  function: string;
  status?: string | null;
}

export interface WsMessage {
  type: "hello" | "ping" | "alert";
  data?: Alert | Record<string, unknown>;
}
