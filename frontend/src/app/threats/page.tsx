"use client";

import { ThreatFeedTable } from "@/components/threats/ThreatFeedTable";
import { useThreats } from "@/hooks/useThreats";

export default function ThreatsPage() {
  const { threats, error } = useThreats();
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Threats</h1>
        <p className="text-sm text-muted">All ingested threat reports and their GenLayer verdicts.</p>
      </div>
      {error && <p className="text-sm text-danger">{error}</p>}
      <ThreatFeedTable threats={threats} />
    </div>
  );
}
