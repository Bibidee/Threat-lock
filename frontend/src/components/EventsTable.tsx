"use client";

import type { EventItem } from "@/lib/types";
import { Card } from "./ui";

function fmtTime(ts: number): string {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

function kindColor(kind: string): string {
  if (kind.includes("PAUSED")) return "text-critical";
  if (kind === "UNPAUSED") return "text-cyan";
  if (kind.includes("AI")) return "text-cyan";
  if (kind.includes("ADMIN")) return "text-secondary";
  return "text-amber";
}

export function EventsTable({
  events,
  error,
}: {
  events: EventItem[];
  error?: string | null;
}) {
  return (
    <Card title="On-chain audit log">
      {error ? (
        <div className="rounded-xl border border-amber/25 bg-amber/[0.06] px-4 py-3 text-sm text-amber">
          {error}
        </div>
      ) : events.length === 0 ? (
        <p className="text-sm text-muted">No events recorded on-chain yet.</p>
      ) : (
        <div className="max-h-[28rem] overflow-y-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-card text-[0.65rem] uppercase tracking-wider text-muted">
              <tr>
                <th className="py-2.5 pr-3 font-semibold">Kind</th>
                <th className="py-2.5 pr-3 font-semibold">Score</th>
                <th className="py-2.5 pr-3 font-semibold">Reason</th>
                <th className="py-2.5 font-semibold">Time</th>
              </tr>
            </thead>
            <tbody>
              {events
                .slice()
                .reverse()
                .map((e, i) => (
                  <tr
                    key={i}
                    className="border-t border-border/60 align-top transition-colors hover:bg-white/[0.02]"
                  >
                    <td className={`py-2.5 pr-3 font-semibold ${kindColor(e.kind)}`}>
                      {e.kind}
                    </td>
                    <td className="py-2.5 pr-3 tabular-nums text-secondary">{e.score}</td>
                    <td className="py-2.5 pr-3 text-secondary">{e.reason}</td>
                    <td className="whitespace-nowrap py-2.5 text-xs text-muted">
                      {fmtTime(e.timestamp)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
