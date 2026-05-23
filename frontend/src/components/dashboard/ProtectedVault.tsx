"use client";

import { useState } from "react";

import { Badge, Button, Card, Dot, Input } from "@/components/ui";
import { useVault } from "@/hooks/useVault";

export function ProtectedVault() {
  const { vault, busy, msg, deposit, withdraw } = useVault();
  const [amount, setAmount] = useState(100);

  return (
    <Card
      title="Protected Vault (Aegis)"
      subtitle="A demo protocol whose withdrawals freeze when Threat-Lock detects an attack"
      right={
        vault?.configured ? (
          vault.frozen ? (
            <Badge tone="red"><Dot tone="red" pulse /> WITHDRAWALS FROZEN</Badge>
          ) : (
            <Badge tone="green"><Dot tone="green" /> WITHDRAWALS OPEN</Badge>
          )
        ) : (
          <Badge tone="neutral">not configured</Badge>
        )
      }
    >
      {!vault?.configured ? (
        <p className="text-sm text-muted">
          Set AEGIS_VAULT_ADDRESS in .env to connect the protected vault.
        </p>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-xl border border-border bg-slate-50 px-4 py-3">
            <span className="text-[0.7rem] uppercase tracking-wide text-muted">Total value locked</span>
            <span className="text-xl font-semibold">{vault.total_locked.toLocaleString()}</span>
          </div>

          {vault.frozen && vault.freeze_reason && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-danger">
              {vault.freeze_reason}
            </div>
          )}

          {msg && (
            <div className={`rounded-lg border px-3 py-2 text-sm ${msg.ok ? "border-blue-200 bg-soft-blue text-primary" : "border-red-200 bg-red-50 text-danger"}`}>
              {msg.text}
            </div>
          )}

          <div className="flex items-end gap-2">
            <div className="flex-1">
              <label className="text-[0.65rem] uppercase tracking-wide text-muted">Amount</label>
              <Input type="number" min={1} value={amount} onChange={(e) => setAmount(Number(e.target.value))} />
            </div>
            <Button variant="ghost" loading={busy === "deposit"} onClick={() => deposit(amount)}>
              Deposit
            </Button>
            <Button variant="primary" loading={busy === "withdraw"} onClick={() => withdraw(amount)}>
              Withdraw
            </Button>
          </div>
          <p className="text-xs text-muted">
            Try a withdrawal, then simulate an active exploit — the next withdrawal is blocked on-chain until an admin recovers.
          </p>
        </div>
      )}
    </Card>
  );
}
