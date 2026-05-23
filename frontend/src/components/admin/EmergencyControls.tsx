"use client";

import { useState } from "react";

import { Badge, Button, Card, Input } from "@/components/ui";
import { useAdminWallet } from "@/hooks/useAdminWallet";
import { manualPause, unpause } from "@/lib/api";
import { shortAddr } from "@/lib/wallet";

export function EmergencyControls({ onDone }: { onDone: () => void }) {
  const { account, adminWallet, available, connecting, isAdmin, connect } = useAdminWallet();
  const [pauseReason, setPauseReason] = useState("Manual emergency pause");
  const [recoveryNote, setRecoveryNote] = useState("Reviewed and cleared");
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function act(name: string, fn: () => Promise<{ message: string }>) {
    setBusy(name);
    setMsg(null);
    try {
      const r = await fn();
      setMsg({ ok: true, text: r.message });
      onDone();
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(null);
    }
  }

  const disabled = !isAdmin;

  return (
    <Card
      title="Emergency controls"
      subtitle="Wallet-authorized contract admin actions"
      right={
        account ? (
          <Badge tone={isAdmin ? "blue" : "amber"}>{isAdmin ? "admin" : "not admin"}</Badge>
        ) : null
      }
    >
      {!available ? (
        <p className="text-sm text-muted">No injected wallet detected. Install a wallet to use admin controls.</p>
      ) : !account ? (
        <Button loading={connecting} onClick={connect}>Connect admin wallet</Button>
      ) : !isAdmin ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-700">
          Connected wallet {shortAddr(account)} is not authorised. Admin wallet is {shortAddr(adminWallet)}.
        </div>
      ) : (
        <div className="space-y-4">
          {msg && (
            <div className={`rounded-lg border px-3 py-2 text-sm ${msg.ok ? "border-blue-200 bg-soft-blue text-primary" : "border-red-200 bg-red-50 text-danger"}`}>
              {msg.text}
            </div>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 rounded-xl border border-red-200 bg-red-50/50 p-3">
              <label className="text-[0.7rem] font-semibold uppercase tracking-wide text-danger">Emergency pause</label>
              <Input value={pauseReason} onChange={(e) => setPauseReason(e.target.value)} disabled={disabled} />
              <Button variant="danger" className="w-full" loading={busy === "pause"}
                onClick={() => act("pause", () => manualPause({ reason: pauseReason, wallet: account }))}>
                Pause system
              </Button>
            </div>
            <div className="space-y-2 rounded-xl border border-border bg-slate-50 p-3">
              <label className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted">Recovery</label>
              <Input value={recoveryNote} onChange={(e) => setRecoveryNote(e.target.value)} disabled={disabled} />
              <Button variant="success" className="w-full" loading={busy === "unpause"}
                onClick={() => act("unpause", () => unpause({ recovery_note: recoveryNote, wallet: account }))}>
                Unpause system
              </Button>
            </div>
          </div>
          <p className="text-xs text-muted">
            Actions are signed by the backend operator. If it isn’t the contract admin, the chain call reverts —
            set GENLAYER_PRIVATE_KEY to the admin key for backend-signed admin actions.
          </p>
        </div>
      )}
    </Card>
  );
}
