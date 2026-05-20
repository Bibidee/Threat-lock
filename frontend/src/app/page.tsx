"use client";

import { useCallback, useEffect, useState } from "react";

import { AlertsPanel } from "@/components/AlertsPanel";
import { ControlPanel } from "@/components/ControlPanel";
import { EventsTable } from "@/components/EventsTable";
import { StatusPanel } from "@/components/StatusPanel";
import { TopBar } from "@/components/TopBar";
import { api } from "@/lib/api";
import type { EventItem, Health, Status } from "@/lib/types";
import { useAlertsSocket } from "@/lib/useAlertsSocket";

const POLL_MS = 10_000;

function msg(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [statusErr, setStatusErr] = useState<string | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [eventsErr, setEventsErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const { alerts, connected, seed } = useAlertsSocket();

  const refresh = useCallback(async () => {
    try {
      setHealth(await api.health());
    } catch {
      setHealth(null);
    }
    try {
      setStatus(await api.getStatus());
      setStatusErr(null);
    } catch (e) {
      setStatus(null);
      setStatusErr(msg(e));
    }
    try {
      setEvents(await api.getEvents(50));
      setEventsErr(null);
    } catch (e) {
      setEvents([]);
      setEventsErr(msg(e));
    }
    setLoading(false);
  }, []);

  const loadAlerts = useCallback(async () => {
    try {
      seed(await api.getAlerts(50));
    } catch {
      /* backend may be down; live socket will fill in */
    }
  }, [seed]);

  useEffect(() => {
    refresh();
    loadAlerts();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh, loadAlerts]);

  return (
    <>
      <TopBar health={health} />
      <main className="mx-auto w-full max-w-7xl flex-1 space-y-6 px-4 py-8 sm:px-6 lg:space-y-8 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-3 lg:gap-8">
          <div className="lg:col-span-1">
            <StatusPanel status={status} error={statusErr} loading={loading} />
          </div>
          <div className="lg:col-span-2">
            <ControlPanel
              onAction={() => {
                refresh();
                loadAlerts();
              }}
            />
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2 lg:gap-8">
          <AlertsPanel alerts={alerts} connected={connected} />
          <EventsTable events={events} error={eventsErr} />
        </div>
      </main>
      <footer className="border-t border-border px-6 py-5 text-center text-[0.7rem] uppercase tracking-[0.16em] text-muted">
        Threat-Lock · GenLayer StudioNet · built locally
      </footer>
    </>
  );
}
