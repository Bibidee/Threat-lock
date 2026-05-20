"use client";

import { useEffect, useState } from "react";

import { Badge, Button } from "./ui";

interface EthProvider {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on?: (event: string, handler: (...args: unknown[]) => void) => void;
  removeListener?: (event: string, handler: (...args: unknown[]) => void) => void;
}

function getEth(): EthProvider | undefined {
  if (typeof window === "undefined") return undefined;
  return (window as unknown as { ethereum?: EthProvider }).ethereum;
}

export function WalletConnect() {
  const [account, setAccount] = useState<string | null>(null);
  const [available, setAvailable] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const eth = getEth();
    setAvailable(!!eth);
    if (!eth) return;

    eth
      .request({ method: "eth_accounts" })
      .then((a) => {
        const arr = a as string[];
        if (arr?.length) setAccount(arr[0]);
      })
      .catch(() => {});

    const onAccounts = (...args: unknown[]) => {
      const arr = args[0] as string[];
      setAccount(arr?.[0] ?? null);
    };
    eth.on?.("accountsChanged", onAccounts);
    return () => eth.removeListener?.("accountsChanged", onAccounts);
  }, []);

  async function connect() {
    const eth = getEth();
    if (!eth) return;
    setBusy(true);
    try {
      const a = await eth.request({ method: "eth_requestAccounts" });
      const arr = a as string[];
      setAccount(arr?.[0] ?? null);
    } catch {
      /* user rejected */
    } finally {
      setBusy(false);
    }
  }

  if (!available) return <Badge tone="muted">No wallet</Badge>;
  if (account)
    return (
      <Badge tone="sky">
        {account.slice(0, 6)}…{account.slice(-4)}
      </Badge>
    );
  return (
    <Button variant="ghost" loading={busy} onClick={connect}>
      Connect wallet
    </Button>
  );
}
