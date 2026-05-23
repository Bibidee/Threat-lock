"use client";

import { Badge, Button, Card, Dot } from "@/components/ui";
import { useMonitoring } from "@/hooks/useMonitoring";

export function MonitoringPanel() {
  const { sources, runs, loading, scanning, error, scan } = useMonitoring();

  return (
    <div className="space-y-6">
      <Card
        title="Monitoring sources"
        subtitle="Real explorer + security/news feeds"
        right={
          <Button loading={scanning} onClick={scan}>
            Run monitoring scan
          </Button>
        }
      >
        {error && <p className="mb-3 text-sm text-danger">{error}</p>}
        {!sources ? (
          <p className="text-sm text-muted">{loading ? "Loading…" : "No source data."}</p>
        ) : (
          <div className="space-y-3">
            <SourceRow
              name="Explorer"
              enabled={sources.explorer.enabled}
              detail={
                sources.explorer.enabled
                  ? `${sources.explorer.provider} · ${sources.explorer.watched_address ?? ""}`
                  : "Not configured (set EXPLORER_API_KEY + watched address)"
              }
            />
            <SourceRow
              name="Security / news (RSS)"
              enabled={sources.news.enabled}
              detail={`${sources.news.source_count} feed(s)`}
            />
            <div className="rounded-lg border border-border bg-slate-50 px-3 py-2.5">
              <p className="text-[0.65rem] uppercase tracking-wide text-muted">Security keywords</p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {sources.security_keywords.map((k) => (
                  <span key={k} className="rounded-md bg-white px-2 py-0.5 text-xs text-slate-600 ring-1 ring-inset ring-border">
                    {k}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </Card>

      <Card title="Recent scans" subtitle="Monitoring run history">
        {runs.length === 0 ? (
          <p className="text-sm text-muted">No scans yet. Click “Run monitoring scan”.</p>
        ) : (
          <ul className="space-y-2">
            {runs.map((r) => (
              <li key={r.id} className="rounded-lg border border-border bg-slate-50 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <Badge tone={r.status === "completed" ? "green" : "amber"}>{r.status}</Badge>
                  <span className="text-xs text-muted">{new Date(r.started_at).toLocaleString()}</span>
                </div>
                <p className="mt-1.5 text-slate-600">
                  sources: {r.sources_checked.join(", ") || "none"} · signals: {r.signals_found} · ingested: {r.threats_ingested}
                  {r.errors.length > 0 ? ` · errors: ${r.errors.length}` : ""}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function SourceRow({ name, enabled, detail }: { name: string; enabled: boolean; detail: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-slate-50 px-3 py-2.5">
      <div className="flex items-center gap-2">
        <Dot tone={enabled ? "green" : "neutral"} />
        <span className="text-sm font-medium text-text">{name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="hidden text-xs text-muted sm:inline">{detail}</span>
        <Badge tone={enabled ? "green" : "neutral"}>{enabled ? "enabled" : "disabled"}</Badge>
      </div>
    </div>
  );
}
