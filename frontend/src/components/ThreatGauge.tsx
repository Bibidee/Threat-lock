"use client";

export function ThreatGauge({
  score,
  threshold,
}: {
  score: number;
  threshold: number;
}) {
  const pct = Math.max(0, Math.min(100, score));
  const color =
    score >= threshold
      ? "bg-red-500"
      : score >= threshold * 0.6
        ? "bg-amber-500"
        : "bg-emerald-500";

  return (
    <div>
      <div className="mb-1 flex items-end justify-between">
        <span className="text-4xl font-bold tabular-nums">{score}</span>
        <span className="text-xs text-muted">/ 100</span>
      </div>
      <div className="relative h-3 w-full overflow-hidden rounded-full bg-surface-2">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
        {/* threshold marker */}
        <div
          className="absolute top-0 h-full w-0.5 bg-foreground/70"
          style={{ left: `${Math.min(100, threshold)}%` }}
          title={`Auto-freeze threshold: ${threshold}`}
        />
      </div>
      <div className="mt-1 text-right text-xs text-muted">
        auto-freeze at {threshold}
      </div>
    </div>
  );
}
