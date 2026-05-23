"use client";

import { Badge, Card, riskTone, verdictTone } from "@/components/ui";
import type { ThreatReport } from "@/types";

export function ThreatConfidenceCard({ latest }: { latest: ThreatReport | null }) {
  return (
    <Card title="Threat confidence" subtitle="Local score vs GenLayer AI verdict">
      {!latest ? (
        <p className="text-sm text-muted">No incidents yet.</p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <Metric label="Local score" value={`${latest.local_score}`} tone={riskTone(latest.risk_level)} />
          <Metric
            label="GenLayer score"
            value={latest.genlayer_score != null ? `${latest.genlayer_score}` : "—"}
            tone={verdictTone(latest.genlayer_verdict)}
          />
          <div className="col-span-2 flex items-center justify-between rounded-lg border border-border bg-slate-50 px-3 py-2.5">
            <span className="text-[0.65rem] uppercase tracking-wide text-muted">Severity / Verdict</span>
            <span className="flex gap-2">
              <Badge tone={riskTone(latest.risk_level)}>{latest.risk_level}</Badge>
              <Badge tone={verdictTone(latest.genlayer_verdict)}>{latest.genlayer_verdict}</Badge>
            </span>
          </div>
        </div>
      )}
    </Card>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone: "neutral" | "blue" | "amber" | "red" | "green" }) {
  const color = { neutral: "text-text", blue: "text-primary", amber: "text-amber", red: "text-danger", green: "text-success" }[tone];
  return (
    <div className="rounded-lg border border-border bg-slate-50 px-3 py-3 text-center">
      <p className="text-[0.65rem] uppercase tracking-wide text-muted">{label}</p>
      <p className={`mt-1 text-3xl font-semibold ${color}`}>{value}</p>
    </div>
  );
}
