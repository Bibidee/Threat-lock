export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const CONTRACT_ADDRESS =
  process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS || "";

export const ADMIN_WALLET_ADDRESS =
  process.env.NEXT_PUBLIC_ADMIN_WALLET_ADDRESS || "";

export const NAV = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Threats", href: "/threats" },
  { label: "Monitoring", href: "/monitoring" },
  { label: "Settings", href: "/settings" },
];
