"use client";

import { useCallback, useEffect, useState } from "react";

import { getAdminConfig } from "@/lib/api";
import { ADMIN_WALLET_ADDRESS } from "@/lib/constants";
import {
  connectWallet,
  currentAccount,
  hasWallet,
  onAccountsChanged,
  sameAddress,
} from "@/lib/wallet";

export function useAdminWallet() {
  const [account, setAccount] = useState<string | null>(null);
  const [adminWallet, setAdminWallet] = useState<string>(ADMIN_WALLET_ADDRESS);
  const [available, setAvailable] = useState(false);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    setAvailable(hasWallet());
    currentAccount().then(setAccount);
    getAdminConfig()
      .then((c) => {
        if (c.admin_wallet_address) setAdminWallet(c.admin_wallet_address);
      })
      .catch(() => {});
    return onAccountsChanged(setAccount);
  }, []);

  const connect = useCallback(async () => {
    setConnecting(true);
    try {
      setAccount(await connectWallet());
    } finally {
      setConnecting(false);
    }
  }, []);

  // Injected wallets can't be force-revoked programmatically; this clears the
  // app's connection state (the user can reconnect with one click).
  const disconnect = useCallback(() => setAccount(null), []);

  const isAdmin = sameAddress(account, adminWallet);

  return { account, adminWallet, available, connecting, isAdmin, connect, disconnect };
}
