"use client";

export function ThreatGauge({
  score,
  threshold,
}: {
  score: number;
  threshold: number;
}) {
  const pct = Math.max(0, Math.min(100, score));
  const high = score >= threshold;
  const mid = !high && score >= threshold * 0.6;
  const bar = high ? "bg-critical" : mid ? "bg-amber" : "bg-cyan";
  const text = high ? "text-critical" : mid ? "text-amber" : "text-cyan";
  const label = high ? "HIGH RISK" : mid ? "ELEVATED" : "NOMINAL";

  return (
    <div>
      <div className="mb-2 flex items-end justify-between">
        <div className="flex items-baseline gap-2">
          <span
            className={`font-display text-5xl font-bold tabular-nums leading-none ${text}`}
          >
            {score}
          </span>
          <span className="text-xs text-muted">/ 100</span>
        </div>
        <span className={`text-[0.7rem] font-semibold uppercase tracking-[0.18em] ${text}`}>
          {label}
        </span>
      </div>
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-elevated">
        <div
          className={`h-full rounded-full transition-all duration-500 ${bar}`}
          style={{ width: `${pct}%` }}
        />
        {/* threshold marker */}
        <div
          className="absolute top-0 h-full w-px bg-foreground/60"
          style={{ left: `${Math.min(100, threshold)}%` }}
          title={`Auto-freeze threshold: ${threshold}`}
        />
      </div>
      <div className="mt-1.5 text-right text-[0.7rem] uppercase tracking-wider text-muted">
        auto-freeze at {threshold}
      </div>
    </div>
  );
}
