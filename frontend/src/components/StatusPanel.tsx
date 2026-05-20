"use client";

import type { Status } from "@/lib/types";
import { Badge, Card } from "./ui";
import { ThreatGauge } from "./ThreatGauge";

export function StatusPanel({
  status,
  error,
  loading,
}: {
  status: Status | null;
  error?: string | null;
  loading: boolean;
}) {
  return (
    <Card
      title="Protocol status"
      right={
        loading ? (
          <Badge tone="muted">refreshing…</Badge>
        ) : status ? (
          status.paused ? (
            <Badge tone="red">● PAUSED</Badge>
          ) : (
            <Badge tone="green">● ACTIVE</Badge>
          )
        ) : null
      }
    >
      {error ? (
        <p className="text-sm text-amber-400">{error}</p>
      ) : !status ? (
        <p className="text-sm text-muted">No contract data yet.</p>
      ) : (
        <div className="space-y-5">
          <div
            className={`rounded-lg border p-4 text-center text-lg font-semibold ${
              status.paused
                ? "border-red-500/40 bg-red-500/10 text-red-400"
                : "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
            }`}
          >
            {status.paused ? "EMERGENCY PAUSE ACTIVE" : "System operating normally"}
          </div>

          <ThreatGauge score={status.threat_score} threshold={status.pause_threshold} />

          <dl className="grid grid-cols-2 gap-3 text-sm">
            <Field label="Events logged" value={String(status.event_count)} />
            <Field label="Threshold" value={String(status.pause_threshold)} />
            <div className="col-span-2">
              <Field
                label="Last reason"
                value={status.last_reason || "—"}
              />
            </div>
            <div className="col-span-2">
              <Field label="Owner" value={status.owner || "—"} mono />
            </div>
          </dl>
        </div>
      )}
    </Card>
  );
}

function Field({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-lg bg-surface-2 px-3 py-2">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className={`mt-0.5 break-all ${mono ? "font-mono text-xs" : ""}`}>
        {value}
      </dd>
    </div>
  );
}
