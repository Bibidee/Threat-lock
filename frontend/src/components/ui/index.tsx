"use client";

import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

type Tone = "neutral" | "blue" | "amber" | "red" | "green";

const TONE: Record<Tone, string> = {
  neutral: "bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200",
  blue: "bg-soft-blue text-primary ring-1 ring-inset ring-blue-200",
  amber: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  red: "bg-red-50 text-danger ring-1 ring-inset ring-red-200",
  green: "bg-green-50 text-success ring-1 ring-inset ring-green-200",
};

export function Card({
  title,
  subtitle,
  right,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card p-5 ${className}`}>
      {(title || right) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title && <h2 className="text-sm font-semibold text-text">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
          </div>
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: Tone }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${TONE[tone]}`}>
      {children}
    </span>
  );
}

export function Dot({ tone = "blue", pulse = false }: { tone?: "blue" | "green" | "amber" | "red" | "neutral"; pulse?: boolean }) {
  const c = { blue: "text-primary", green: "text-success", amber: "text-amber", red: "text-danger", neutral: "text-slate-400" }[tone];
  return <span className={`tl-dot ${pulse ? "tl-dot--pulse" : ""} ${c}`} />;
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "danger" | "success" | "ghost";
  loading?: boolean;
};

export function Button({ variant = "primary", loading = false, disabled, children, className = "", ...rest }: ButtonProps) {
  const styles: Record<string, string> = {
    primary: "bg-primary text-white hover:brightness-110 shadow-sm",
    danger: "bg-danger text-white hover:brightness-110 shadow-sm",
    success: "bg-success text-white hover:brightness-110 shadow-sm",
    ghost: "bg-white text-text border border-border hover:bg-slate-50",
  };
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`}
    >
      {loading && <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current/30 border-t-current" />}
      {children}
    </button>
  );
}

export function Input({ className = "", ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...rest}
      className={`w-full rounded-lg border border-border bg-white px-3.5 py-2.5 text-sm text-text placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/15 ${className}`}
    />
  );
}

export function Textarea({ className = "", ...rest }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...rest}
      className={`w-full rounded-lg border border-border bg-white px-3.5 py-2.5 text-sm leading-relaxed text-text placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/15 ${className}`}
    />
  );
}

export function Stat({ label, value, tone = "neutral", foot }: { label: string; value: ReactNode; tone?: Tone; foot?: ReactNode }) {
  const valueColor = { neutral: "text-text", blue: "text-primary", amber: "text-amber", red: "text-danger", green: "text-success" }[tone];
  return (
    <div className="card p-5">
      <p className="text-[0.7rem] font-medium uppercase tracking-wide text-muted">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${valueColor}`}>{value}</p>
      {foot && <p className="mt-1 text-xs text-muted">{foot}</p>}
    </div>
  );
}

export function riskTone(level?: string): Tone {
  switch ((level || "").toLowerCase()) {
    case "critical": return "red";
    case "medium":
    case "elevated": return "amber";
    case "low":
    case "normal": return "green";
    default: return "neutral";
  }
}

export function verdictTone(v?: string): Tone {
  switch ((v || "").toUpperCase()) {
    case "CRITICAL": return "red";
    case "SUSPICIOUS": return "amber";
    case "SAFE": return "green";
    default: return "neutral";
  }
}
