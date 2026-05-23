"use client";

import { useCallback, useEffect, useState } from "react";

import { getVaultStatus, vaultDeposit, vaultWithdraw } from "@/lib/api";
import type { VaultStatus } from "@/types";

export function useVault(pollMs = 10000) {
  const [vault, setVault] = useState<VaultStatus | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const refresh = useCallback(async () => {
    try {
      setVault(await getVaultStatus());
    } catch {
      setVault(null);
    }
  }, []);

  const deposit = useCallback(async (amount: number) => {
    setBusy("deposit");
    setMsg(null);
    try {
      await vaultDeposit(amount);
      setMsg({ ok: true, text: `Deposited ${amount}` });
      await refresh();
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(null);
    }
  }, [refresh]);

  const withdraw = useCallback(async (amount: number) => {
    setBusy("withdraw");
    setMsg(null);
    try {
      await vaultWithdraw(amount);
      setMsg({ ok: true, text: `Withdrew ${amount}` });
      await refresh();
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(null);
    }
  }, [refresh]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, pollMs);
    return () => clearInterval(id);
  }, [refresh, pollMs]);

  return { vault, busy, msg, deposit, withdraw, refresh };
}
