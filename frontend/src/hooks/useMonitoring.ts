"use client";

import { useCallback, useEffect, useState } from "react";

import { getMonitoringRuns, getMonitoringSources, runMonitoringScan } from "@/lib/api";
import type { MonitoringRun, MonitoringSources } from "@/types";

export function useMonitoring() {
  const [sources, setSources] = useState<MonitoringSources | null>(null);
  const [runs, setRuns] = useState<MonitoringRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, r] = await Promise.all([getMonitoringSources(), getMonitoringRuns(20)]);
      setSources(s);
      setRuns(r);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setLoading(false);
  }, []);

  const scan = useCallback(async () => {
    setScanning(true);
    try {
      await runMonitoringScan();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setScanning(false);
    }
  }, [refresh]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { sources, runs, loading, scanning, error, refresh, scan };
}
