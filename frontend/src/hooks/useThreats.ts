"use client";

import { useCallback, useEffect, useState } from "react";

import { getLatestThreat, getThreats } from "@/lib/api";
import type { ThreatReport } from "@/types";

export function useThreats(pollMs = 12000) {
  const [threats, setThreats] = useState<ThreatReport[]>([]);
  const [latest, setLatest] = useState<ThreatReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [list, last] = await Promise.all([getThreats(50), getLatestThreat()]);
      setThreats(list);
      setLatest(last);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, pollMs);
    return () => clearInterval(id);
  }, [refresh, pollMs]);

  return { threats, latest, loading, error, refresh };
}
