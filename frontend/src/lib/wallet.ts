// Injected-wallet helpers (MetaMask-style window.ethereum). No external kits.

interface EthProvider {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on?: (event: string, handler: (...args: unknown[]) => void) => void;
  removeListener?: (event: string, handler: (...args: unknown[]) => void) => void;
}

export function getEthereum(): EthProvider | undefined {
  if (typeof window === "undefined") return undefined;
  return (window as unknown as { ethereum?: EthProvider }).ethereum;
}

export function hasWallet(): boolean {
  return !!getEthereum();
}

export async function connectWallet(): Promise<string | null> {
  const eth = getEthereum();
  if (!eth) return null;
  const accounts = (await eth.request({ method: "eth_requestAccounts" })) as string[];
  return accounts?.[0] ?? null;
}

export async function currentAccount(): Promise<string | null> {
  const eth = getEthereum();
  if (!eth) return null;
  try {
    const accounts = (await eth.request({ method: "eth_accounts" })) as string[];
    return accounts?.[0] ?? null;
  } catch {
    return null;
  }
}

export function onAccountsChanged(handler: (account: string | null) => void): () => void {
  const eth = getEthereum();
  if (!eth?.on) return () => {};
  const cb = (...args: unknown[]) => handler(((args[0] as string[]) ?? [])[0] ?? null);
  eth.on("accountsChanged", cb);
  return () => eth.removeListener?.("accountsChanged", cb);
}

export function sameAddress(a?: string | null, b?: string | null): boolean {
  return !!a && !!b && a.toLowerCase() === b.toLowerCase();
}

export function shortAddr(a?: string | null): string {
  if (!a) return "";
  return a.length > 12 ? `${a.slice(0, 6)}…${a.slice(-4)}` : a;
}
