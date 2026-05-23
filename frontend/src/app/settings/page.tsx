"use client";

import { useEffect, useState } from "react";

import { Badge, Card } from "@/components/ui";
import { getAdminConfig, getHealth } from "@/lib/api";
import type { AdminConfig, Health } from "@/types";

export default function SettingsPage() {
  const [config, setConfig] = useState<AdminConfig | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminConfig().then(setConfig).catch((e) => setError(String(e?.message ?? e)));
    getHealth().then(setHealth).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Settings</h1>
        <p className="text-sm text-muted">Backend, GenLayer, and admin configuration.</p>
      </div>
      {error && <p className="text-sm text-danger">{error}</p>}

      <Card title="GenLayer">
        <Row label="Mode" value={<Badge tone={config?.genlayer_mode === "real" ? "green" : "amber"}>{config?.genlayer_mode ?? "…"}</Badge>} />
        <Row label="Contract address" value={config?.genlayer_contract_address || "—"} mono />
        <Row label="Admin wallet" value={config?.admin_wallet_address || "—"} mono />
      </Card>

      <Card title="Backend">
        <Row label="Service" value={health?.service ?? "—"} />
        <Row label="Firebase backend" value={<Badge tone={health?.firebase_backend === "firestore" ? "green" : "neutral"}>{health?.firebase_backend ?? "…"}</Badge>} />
        <Row label="Health" value={<Badge tone={health?.ok ? "green" : "red"}>{health?.ok ? "ok" : "down"}</Badge>} />
      </Card>
    </div>
  );
}

function Row({ label, value, mono = false }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 py-2.5 last:border-0">
      <span className="text-sm text-muted">{label}</span>
      <span className={`text-sm text-text ${mono ? "font-mono text-xs break-all" : ""}`}>{value}</span>
    </div>
  );
}
