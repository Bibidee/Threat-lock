"use client";

import { MonitoringPanel } from "@/components/monitoring/MonitoringPanel";

export default function MonitoringPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Monitoring</h1>
        <p className="text-sm text-muted">Live sources, manual scans, and scan history.</p>
      </div>
      <MonitoringPanel />
    </div>
  );
}
