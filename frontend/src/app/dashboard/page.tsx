"use client";

import { EmergencyControls } from "@/components/admin/EmergencyControls";
import { ProtectedVault } from "@/components/dashboard/ProtectedVault";
import { LatestIncidentPanel } from "@/components/dashboard/LatestIncidentPanel";
import { SimulationPanel } from "@/components/dashboard/SimulationPanel";
import { SystemStatusCard } from "@/components/dashboard/SystemStatusCard";
import { ThreatConfidenceCard } from "@/components/dashboard/ThreatConfidenceCard";
import { ThreatFeedTable } from "@/components/threats/ThreatFeedTable";
import { useSystemStatus } from "@/hooks/useSystemStatus";
import { useThreats } from "@/hooks/useThreats";

export default function DashboardPage() {
  const { status, error, loading, refresh } = useSystemStatus();
  const { threats, latest, refresh: refreshThreats } = useThreats();

  const refreshAll = () => {
    refresh();
    refreshThreats();
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-3">
        <SystemStatusCard status={status} error={error} loading={loading} />
        <ThreatConfidenceCard latest={latest} />
        <SimulationPanel onDone={refreshAll} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <LatestIncidentPanel latest={latest} />
        <EmergencyControls onDone={refreshAll} />
      </div>

      <ProtectedVault />

      <ThreatFeedTable threats={threats.slice(0, 8)} />
    </div>
  );
}
