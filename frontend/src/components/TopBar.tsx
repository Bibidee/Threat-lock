"use client";

import { useState } from "react";

import { useAuth } from "@/lib/auth";
import type { Health } from "@/lib/types";
import { Badge, Button, Dot, Input } from "./ui";
import { WalletConnect } from "./WalletConnect";

export function TopBar({ health }: { health: Health | null }) {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan font-display text-base font-bold text-black shadow-[0_0_28px_-8px_var(--cyan)]">
            TL
          </div>
          <div>
            <h1 className="font-display text-lg font-semibold leading-tight tracking-tight">
              Threat-Lock
            </h1>
            <p className="text-[0.7rem] uppercase tracking-[0.16em] text-muted">
              Security Command Centre
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <HealthBadges health={health} />
          <WalletConnect />
          <AuthControl />
        </div>
      </div>
    </header>
  );
}

function HealthBadges({ health }: { health: Health | null }) {
  if (!health) return <Badge tone="amber">backend offline</Badge>;
  return (
    <>
      <Badge tone="cyan">
        <Dot tone="cyan" pulse /> {health.genlayer_network}
      </Badge>
      <Badge tone={health.contract_configured ? "cyan" : "muted"}>
        contract {health.contract_configured ? "set" : "—"}
      </Badge>
      <Badge tone={health.write_enabled ? "cyan" : "amber"}>
        writes {health.write_enabled ? "on" : "off"}
      </Badge>
      <Badge tone={health.firebase_enabled ? "cyan" : "muted"}>
        firebase {health.firebase_enabled ? "on" : "off"}
      </Badge>
    </>
  );
}

function AuthControl() {
  const { configured, user, login, logout, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  if (loading) return <Badge tone="muted">…</Badge>;
  if (!configured) return <Badge tone="amber">dev mode</Badge>;

  if (user) {
    return (
      <div className="flex items-center gap-2">
        <Badge tone="cyan">{user.email ?? "signed in"}</Badge>
        <Button variant="ghost" onClick={() => logout()}>
          Sign out
        </Button>
      </div>
    );
  }

  async function doLogin() {
    setBusy(true);
    setErr(null);
    try {
      await login(email, password);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Input
        type="email"
        placeholder="admin email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-40"
      />
      <Input
        type="password"
        placeholder="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="w-32"
      />
      <Button loading={busy} onClick={doLogin}>
        Sign in
      </Button>
      {err && <span className="text-xs text-critical">{err}</span>}
    </div>
  );
}
