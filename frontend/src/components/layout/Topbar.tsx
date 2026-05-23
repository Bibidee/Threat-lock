"use client";

import { Badge, Button, Dot } from "@/components/ui";
import { useAdminWallet } from "@/hooks/useAdminWallet";
import { useSystemStatus } from "@/hooks/useSystemStatus";
import { shortAddr } from "@/lib/wallet";

export function Topbar() {
  const { status } = useSystemStatus();
  const { account, available, connecting, isAdmin, connect, disconnect } = useAdminWallet();

  return (
    <header className="sticky top-0 z-10 border-b border-border bg-white/90 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar text-xs font-bold text-white lg:hidden">
            TL
          </div>
          <div>
            <h1 className="text-base font-semibold leading-tight">Security Operations</h1>
            <p className="text-[0.7rem] text-muted">Protocol threat monitoring &amp; emergency response</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {status ? (
            status.paused ? (
              <Badge tone="red"><Dot tone="red" pulse /> PAUSED</Badge>
            ) : (
              <Badge tone="green"><Dot tone="green" pulse /> ACTIVE</Badge>
            )
          ) : (
            <Badge tone="neutral">…</Badge>
          )}

          {!available ? (
            <Badge tone="neutral">No wallet</Badge>
          ) : account ? (
            <div className="flex items-center gap-2">
              <Badge tone={isAdmin ? "blue" : "amber"}>
                <Dot tone={isAdmin ? "blue" : "amber"} /> {shortAddr(account)}{isAdmin ? " · admin" : ""}
              </Badge>
              <Button variant="ghost" onClick={disconnect}>Disconnect</Button>
            </div>
          ) : (
            <Button variant="ghost" loading={connecting} onClick={connect}>
              Connect wallet
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
