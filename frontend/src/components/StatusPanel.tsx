"use client";

import type { Status } from "@/lib/types";
import { Badge, Card, Dot } from "./ui";
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
            <Badge tone="critical">
              <Dot tone="critical" pulse /> PAUSED
            </Badge>
          ) : (
            <Badge tone="cyan">
              <Dot tone="cyan" pulse /> ACTIVE
            </Badge>
          )
        ) : null
      }
    >
      {error ? (
        <div className="rounded-xl border border-amber/25 bg-amber/[0.06] px-4 py-3 text-sm text-amber">
          {error}
        </div>
      ) : !status ? (
        <p className="text-sm text-muted">No contract data yet.</p>
      ) : (
        <div className="space-y-5">
          <div
            className={`rounded-xl border p-4 text-center text-base font-semibold tracking-tight ${
              status.paused
                ? "tl-critical-glow border-critical/40 bg-critical/10 text-critical"
                : "border-cyan/30 bg-cyan/[0.07] text-cyan"
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
    <div className="rounded-xl border border-border bg-elevated/60 px-3.5 py-2.5">
      <dt className="text-[0.65rem] uppercase tracking-wider text-muted">{label}</dt>
      <dd className={`mt-1 break-all text-secondary ${mono ? "font-mono text-xs" : ""}`}>
        {value}
      </dd>
    </div>
  );
}
