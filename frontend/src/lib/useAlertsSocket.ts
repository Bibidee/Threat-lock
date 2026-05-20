"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { BACKEND_URL } from "./api";
import type { Alert, WsMessage } from "./types";

function wsUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_WS_URL;
  if (explicit) return explicit;
  return `${BACKEND_URL.replace(/^http/, "ws")}/ws/alerts`;
}

export function useAlertsSocket() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const pushAlert = useCallback((a: Alert) => {
    setAlerts((prev) => [a, ...prev].slice(0, 100));
  }, []);

  const seed = useCallback((items: Alert[]) => setAlerts(items), []);

  useEffect(() => {
    let stopped = false;
    let retry: ReturnType<typeof setTimeout> | undefined;

    function connect() {
      let ws: WebSocket;
      try {
        ws = new WebSocket(wsUrl());
      } catch {
        retry = setTimeout(connect, 3000);
        return;
      }
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!stopped) retry = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data) as WsMessage;
          if (msg.type === "alert" && msg.data) pushAlert(msg.data as Alert);
        } catch {
          /* ignore malformed frames */
        }
      };
    }

    connect();
    return () => {
      stopped = true;
      if (retry) clearTimeout(retry);
      wsRef.current?.close();
    };
  }, [pushAlert]);

  return { alerts, connected, seed, pushAlert };
}
