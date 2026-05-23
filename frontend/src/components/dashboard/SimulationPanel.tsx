"use client";

import { useState } from "react";

import { Button, Card } from "@/components/ui";
import { simulateActiveExploit, simulateNormalActivity, simulateSuspiciousWallet } from "@/lib/api";
import type { ThreatResult } from "@/types";

export function SimulationPanel({ onDone }: { onDone: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function run(name: string, fn: () => Promise<ThreatResult>) {
    setBusy(name);
    setMsg(null);
    try {
      const r = await fn();
      setMsg({
        ok: true,
        text: `${name}: risk=${r.risk_level}, verdict=${r.genlayer_verdict}, action=${r.action}${
          r.pause_triggered ? " — PAUSE TRIGGERED" : ""
        }`,
      });
      onDone();
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card title="Simulate threat" subtitle="Drive the full detection pipeline (test buttons)">
      {msg && (
        <div
          className={`mb-3 rounded-lg border px-3 py-2 text-sm ${
            msg.ok ? "border-blue-200 bg-soft-blue text-primary" : "border-red-200 bg-red-50 text-danger"
          }`}
        >
          {msg.text}
        </div>
      )}
      <div className="grid gap-2 sm:grid-cols-3">
        <Button variant="ghost" loading={busy === "Normal activity"} onClick={() => run("Normal activity", simulateNormalActivity)}>
          Normal activity
        </Button>
        <Button variant="ghost" loading={busy === "Suspicious wallet"} onClick={() => run("Suspicious wallet", simulateSuspiciousWallet)}>
          Suspicious wallet
        </Button>
        <Button variant="danger" loading={busy === "Active exploit"} onClick={() => run("Active exploit", simulateActiveExploit)}>
          Active exploit
        </Button>
      </div>
      <p className="mt-2 text-xs text-muted">
        “Active exploit” sends evidence to the on-chain GenLayer AI judge and can auto-pause the contract.
      </p>
    </Card>
  );
}
