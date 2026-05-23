"use client";

import { Badge, Card, riskTone, verdictTone } from "@/components/ui";
import type { ThreatReport } from "@/types";

export function LatestIncidentPanel({ latest }: { latest: ThreatReport | null }) {
  return (
    <Card title="Latest incident" subtitle="Most recent threat report and AI judgment">
      {!latest ? (
        <p className="text-sm text-muted">No incidents recorded yet. Run a scan or simulate a threat.</p>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={riskTone(latest.risk_level)}>{latest.risk_level}</Badge>
            <Badge tone={verdictTone(latest.genlayer_verdict)}>{latest.genlayer_verdict}</Badge>
            {latest.pause_triggered && <Badge tone="red">PAUSE TRIGGERED</Badge>}
            <span className="ml-auto font-mono text-xs text-muted">{latest.id}</span>
          </div>

          <p className="text-sm font-medium text-text">{latest.description || latest.evidence.slice(0, 160)}</p>
          <p className="rounded-lg border border-border bg-slate-50 px-3 py-2 text-sm text-slate-600">{latest.evidence}</p>

          {latest.genlayer_reasoning && (
            <div className="rounded-lg border border-blue-200 bg-soft-blue px-3 py-2">
              <p className="text-[0.65rem] uppercase tracking-wide text-primary">GenLayer AI reasoning</p>
              <p className="mt-1 text-sm text-slate-700">{latest.genlayer_reasoning}</p>
            </div>
          )}

          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-3">
            <Field label="Protocol" value={latest.protocol} />
            <Field label="Source" value={latest.source} />
            <Field label="Event" value={latest.event_type} />
            <Field label="Recommended" value={latest.genlayer_recommended_action || "—"} />
            <Field label="Amount (USD)" value={latest.amount_usd ? `$${Number(latest.amount_usd).toLocaleString()}` : "—"} />
            <Field label="Tx count" value={`${latest.tx_count ?? 0}`} />
            {latest.wallet && <Field label="Wallet" value={latest.wallet} mono />}
            {latest.source_url && (
              <div className="col-span-2 sm:col-span-3">
                <dt className="text-[0.65rem] uppercase tracking-wide text-muted">Source URL</dt>
                <dd className="mt-0.5">
                  <a href={latest.source_url} target="_blank" rel="noreferrer" className="break-all text-sm text-primary hover:underline">
                    {latest.source_url}
                  </a>
                </dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </Card>
  );
}

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-[0.65rem] uppercase tracking-wide text-muted">{label}</dt>
      <dd className={`mt-0.5 break-all text-text ${mono ? "font-mono text-xs" : ""}`}>{value}</dd>
    </div>
  );
}
