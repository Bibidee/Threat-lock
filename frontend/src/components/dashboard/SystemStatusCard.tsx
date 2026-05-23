"use client";

import { Badge, Card, Dot, riskTone, verdictTone } from "@/components/ui";
import type { SystemStatus } from "@/types";

export function SystemStatusCard({
  status,
  error,
  loading,
}: {
  status: SystemStatus | null;
  error?: string | null;
  loading: boolean;
}) {
  return (
    <Card title="System status" subtitle="Live protocol protection state">
      {error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">{error}</div>
      ) : !status ? (
        <p className="text-sm text-muted">{loading ? "Loading…" : "No data."}</p>
      ) : (
        <div className="space-y-4">
          <div
            className={`flex items-center justify-between rounded-xl border p-4 ${
              status.paused ? "border-red-200 bg-red-50" : "border-green-200 bg-green-50"
            }`}
          >
            <div>
              <p className="text-[0.7rem] uppercase tracking-wide text-muted">Protection</p>
              <p className={`text-xl font-semibold ${status.paused ? "text-danger" : "text-success"}`}>
                {status.paused ? "PAUSED" : "ACTIVE"}
              </p>
            </div>
            <Dot tone={status.paused ? "red" : "green"} pulse />
          </div>

          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg border border-border bg-slate-50 px-3 py-2">
              <dt className="text-[0.65rem] uppercase tracking-wide text-muted">Risk level</dt>
              <dd className="mt-1"><Badge tone={riskTone(status.risk_level)}>{status.risk_level}</Badge></dd>
            </div>
            <div className="rounded-lg border border-border bg-slate-50 px-3 py-2">
              <dt className="text-[0.65rem] uppercase tracking-wide text-muted">Latest verdict</dt>
              <dd className="mt-1"><Badge tone={verdictTone(status.latest_verdict)}>{status.latest_verdict}</Badge></dd>
            </div>
            <div className="col-span-2 rounded-lg border border-border bg-slate-50 px-3 py-2">
              <dt className="text-[0.65rem] uppercase tracking-wide text-muted">Last action</dt>
              <dd className="mt-1 text-text">{status.last_action}</dd>
            </div>
          </dl>
          <p className="text-xs text-muted">Updated {new Date(status.updated_at).toLocaleString()}</p>
        </div>
      )}
    </Card>
  );
}
