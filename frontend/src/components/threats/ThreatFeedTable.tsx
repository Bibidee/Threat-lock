"use client";

import { Badge, Card, riskTone, verdictTone } from "@/components/ui";
import { formatUtc } from "@/lib/format";
import type { ThreatReport } from "@/types";

export function ThreatFeedTable({ threats }: { threats: ThreatReport[] }) {
  return (
    <Card title="Threat feed" subtitle="Recent threat reports">
      {threats.length === 0 ? (
        <p className="text-sm text-muted">No threat reports yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border text-[0.65rem] uppercase tracking-wide text-muted">
              <tr>
                <th className="py-2 pr-3 font-medium">Report</th>
                <th className="py-2 pr-3 font-medium">Event</th>
                <th className="py-2 pr-3 font-medium">Source</th>
                <th className="py-2 pr-3 font-medium">Severity</th>
                <th className="py-2 pr-3 font-medium">Score</th>
                <th className="py-2 pr-3 font-medium">Verdict</th>
                <th className="py-2 pr-3 font-medium">Pause</th>
                <th className="py-2 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {threats.map((t) => (
                <tr key={t.id} className="border-b border-border/60 align-top hover:bg-slate-50">
                  <td className="py-2.5 pr-3 font-mono text-xs text-muted">{t.id.slice(0, 14)}…</td>
                  <td className="py-2.5 pr-3">{t.event_type}</td>
                  <td className="py-2.5 pr-3 text-muted">{t.source}</td>
                  <td className="py-2.5 pr-3"><Badge tone={riskTone(t.risk_level)}>{t.risk_level}</Badge></td>
                  <td className="py-2.5 pr-3 tabular-nums">{t.local_score}{t.genlayer_score != null ? ` / ${t.genlayer_score}` : ""}</td>
                  <td className="py-2.5 pr-3"><Badge tone={verdictTone(t.genlayer_verdict)}>{t.genlayer_verdict}</Badge></td>
                  <td className="py-2.5 pr-3">{t.pause_triggered ? <Badge tone="red">yes</Badge> : <span className="text-muted">—</span>}</td>
                  <td className="whitespace-nowrap py-2.5 text-xs text-muted">{formatUtc(t.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
