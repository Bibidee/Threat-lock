"use client";

import { useCallback, useEffect, useState } from "react";

import { getHealth, getSystemStatus } from "@/lib/api";
import type { Health, SystemStatus } from "@/types";

export function useSystemStatus(pollMs = 10000) {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setStatus(await getSystemStatus());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    try {
      setHealth(await getHealth());
    } catch {
      setHealth(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, pollMs);
    return () => clearInterval(id);
  }, [refresh, pollMs]);

  return { status, health, error, loading, refresh };
}
