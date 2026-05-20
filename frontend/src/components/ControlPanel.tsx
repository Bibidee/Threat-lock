"use client";

import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { TxResponse } from "@/lib/types";
import { Badge, Button, Card, Input, Textarea } from "./ui";

type Msg = { ok: boolean; text: string } | null;

export function ControlPanel({ onAction }: { onAction: () => void }) {
  const { canControl, configured, getToken } = useAuth();
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<Msg>(null);

  // form state
  const [score, setScore] = useState(80);
  const [reportReason, setReportReason] = useState("Manual report from dashboard");
  const [evidence, setEvidence] = useState("");
  const [pauseReason, setPauseReason] = useState("Manual emergency pause");
  const [unpauseReason, setUnpauseReason] = useState("Threat cleared");
  const [threshold, setThreshold] = useState(75);

  async function run(name: string, fn: (token: string | null) => Promise<TxResponse>) {
    setBusy(name);
    setMsg(null);
    try {
      const token = await getToken();
      const res = await fn(token);
      setMsg({ ok: true, text: `${res.function} sent — ${res.status ?? "submitted"} (${short(res.tx_hash)})` });
      onAction();
    } catch (e) {
      const detail = e instanceof ApiError ? e.message : String(e);
      setMsg({ ok: false, text: detail });
    } finally {
      setBusy(null);
    }
  }

  const disabled = !canControl;

  return (
    <Card
      title="Emergency controls"
      right={
        disabled ? <Badge tone="amber">sign in to control</Badge> : <Badge tone="sky">ready</Badge>
      }
    >
      {!configured && (
        <p className="mb-3 text-xs text-muted">
          Dev mode: Firebase not configured, actions are unauthenticated.
        </p>
      )}

      {msg && (
        <div
          className={`mb-4 rounded-lg border px-3 py-2 text-sm ${
            msg.ok
              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
              : "border-red-500/40 bg-red-500/10 text-red-300"
          }`}
        >
          {msg.text}
        </div>
      )}

      <div className="grid gap-5 md:grid-cols-2">
        {/* Pause / Unpause */}
        <div className="space-y-2">
          <Label>Manual pause</Label>
          <Input
            value={pauseReason}
            onChange={(e) => setPauseReason(e.target.value)}
            placeholder="Reason"
            disabled={disabled}
          />
          <Button
            variant="danger"
            disabled={disabled}
            loading={busy === "pause"}
            onClick={() => run("pause", (t) => api.pause({ reason: pauseReason }, t))}
            className="w-full"
          >
            Emergency pause
          </Button>
        </div>

        <div className="space-y-2">
          <Label>Recovery</Label>
          <Input
            value={unpauseReason}
            onChange={(e) => setUnpauseReason(e.target.value)}
            placeholder="Reason"
            disabled={disabled}
          />
          <Button
            variant="primary"
            disabled={disabled}
            loading={busy === "unpause"}
            onClick={() => run("unpause", (t) => api.unpause({ reason: unpauseReason }, t))}
            className="w-full"
          >
            Unpause
          </Button>
        </div>

        {/* Report threat */}
        <div className="space-y-2">
          <Label>Report threat score (0–100)</Label>
          <div className="flex gap-2">
            <Input
              type="number"
              min={0}
              max={100}
              value={score}
              onChange={(e) => setScore(Number(e.target.value))}
              disabled={disabled}
              className="w-24"
            />
            <Input
              value={reportReason}
              onChange={(e) => setReportReason(e.target.value)}
              placeholder="Reason"
              disabled={disabled}
            />
          </div>
          <Button
            variant="warn"
            disabled={disabled}
            loading={busy === "report"}
            onClick={() =>
              run("report", (t) =>
                api.report({ score, reason: reportReason, source: "dashboard" }, t),
              )
            }
            className="w-full"
          >
            Submit report
          </Button>
        </div>

        {/* Set threshold */}
        <div className="space-y-2">
          <Label>Auto-freeze threshold</Label>
          <Input
            type="number"
            min={0}
            max={100}
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            disabled={disabled}
          />
          <Button
            variant="ghost"
            disabled={disabled}
            loading={busy === "threshold"}
            onClick={() =>
              run("threshold", (t) => api.setThreshold({ new_threshold: threshold }, t))
            }
            className="w-full"
          >
            Update threshold
          </Button>
        </div>

        {/* AI verify */}
        <div className="space-y-2 md:col-span-2">
          <Label>AI threat verification (LLM decides)</Label>
          <Textarea
            rows={3}
            value={evidence}
            onChange={(e) => setEvidence(e.target.value)}
            placeholder="Paste evidence: suspicious tx pattern, exploit report, news snippet…"
            disabled={disabled}
          />
          <Button
            variant="warn"
            disabled={disabled || evidence.trim().length === 0}
            loading={busy === "verify"}
            onClick={() => run("verify", (t) => api.verify({ evidence }, t))}
            className="w-full md:w-auto"
          >
            Run AI verification
          </Button>
        </div>
      </div>
    </Card>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-xs font-medium text-muted">{children}</label>;
}

function short(h: string): string {
  return h && h.length > 12 ? `${h.slice(0, 8)}…${h.slice(-4)}` : h;
}
