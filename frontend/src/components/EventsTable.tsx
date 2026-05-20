"use client";

import type { EventItem } from "@/lib/types";
import { Card } from "./ui";

function fmtTime(ts: number): string {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

function kindColor(kind: string): string {
  if (kind.includes("PAUSED")) return "text-red-400";
  if (kind === "UNPAUSED") return "text-emerald-400";
  if (kind.includes("AI")) return "text-sky-400";
  if (kind.includes("ADMIN")) return "text-violet-400";
  return "text-amber-400";
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
        <p className="text-sm text-amber-400">{error}</p>
      ) : events.length === 0 ? (
        <p className="text-sm text-muted">No events recorded on-chain yet.</p>
      ) : (
        <div className="max-h-[28rem] overflow-y-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-surface text-xs uppercase text-muted">
              <tr>
                <th className="py-2 pr-3">Kind</th>
                <th className="py-2 pr-3">Score</th>
                <th className="py-2 pr-3">Reason</th>
                <th className="py-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {events
                .slice()
                .reverse()
                .map((e, i) => (
                  <tr key={i} className="border-t border-border/60 align-top">
                    <td className={`py-2 pr-3 font-medium ${kindColor(e.kind)}`}>
                      {e.kind}
                    </td>
                    <td className="py-2 pr-3 tabular-nums">{e.score}</td>
                    <td className="py-2 pr-3 text-muted">{e.reason}</td>
                    <td className="whitespace-nowrap py-2 text-xs text-muted">
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
