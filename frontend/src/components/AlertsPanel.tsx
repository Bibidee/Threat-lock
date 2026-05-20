"use client";

import type { Alert } from "@/lib/types";
import { Badge, Card } from "./ui";

function severityTone(sev?: string): "red" | "amber" | "sky" | "muted" {
  switch (sev) {
    case "critical":
      return "red";
    case "warning":
      return "amber";
    case "info":
      return "sky";
    default:
      return "muted";
  }
}

function timeAgo(ts?: number): string {
  if (!ts) return "";
  const secs = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}

export function AlertsPanel({
  alerts,
  connected,
}: {
  alerts: Alert[];
  connected: boolean;
}) {
  return (
    <Card
      title="Live alerts"
      right={
        connected ? (
          <Badge tone="green">● live</Badge>
        ) : (
          <Badge tone="muted">○ offline</Badge>
        )
      }
    >
      {alerts.length === 0 ? (
        <p className="text-sm text-muted">No alerts yet. Monitoring is watching…</p>
      ) : (
        <ul className="max-h-[28rem] space-y-2 overflow-y-auto pr-1">
          {alerts.map((a, i) => (
            <li
              key={a.id ?? i}
              className="rounded-lg border border-border bg-surface-2 p-3"
            >
              <div className="flex items-center justify-between gap-2">
                <Badge tone={severityTone(a.severity)}>
                  {(a.severity ?? "info").toUpperCase()}
                </Badge>
                <span className="text-xs text-muted">{timeAgo(a.created_at)}</span>
              </div>
              <p className="mt-1.5 text-sm">{a.reason ?? a.kind ?? "alert"}</p>
              <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted">
                {a.kind && <span>kind: {a.kind}</span>}
                {typeof a.score === "number" && <span>score: {a.score}</span>}
                {a.source && <span>src: {a.source}</span>}
                {a.tx_hash && <span className="font-mono">tx: {a.tx_hash.slice(0, 10)}…</span>}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
