"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

type Tone = "muted" | "cyan" | "critical" | "amber";

export function Card({
  title,
  right,
  children,
  className = "",
}: {
  title?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`card-hover rounded-2xl border border-border bg-card/80 p-6 shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset] backdrop-blur-sm ${className}`}
    >
      {(title || right) && (
        <div className="mb-5 flex items-center justify-between gap-3">
          {title && (
            <h2 className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-muted">
              {title}
            </h2>
          )}
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "danger" | "ghost" | "warn";
  loading?: boolean;
};

export function Button({
  variant = "primary",
  loading = false,
  disabled,
  children,
  className = "",
  ...rest
}: ButtonProps) {
  const styles: Record<string, string> = {
    primary:
      "bg-cyan text-black hover:brightness-110 shadow-[0_0_24px_-10px_var(--cyan)]",
    danger:
      "bg-critical text-white hover:brightness-110 shadow-[0_0_28px_-10px_var(--critical)]",
    warn: "bg-amber text-black hover:brightness-110 shadow-[0_0_24px_-12px_var(--amber)]",
    ghost:
      "bg-elevated text-foreground border border-border hover:border-border-hover",
  };
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold tracking-tight transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/50 disabled:cursor-not-allowed disabled:opacity-40 ${styles[variant]} ${className}`}
    >
      {loading && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current/30 border-t-current" />
      )}
      {children}
    </button>
  );
}

export function Input({
  className = "",
  ...rest
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...rest}
      className={`w-full rounded-xl border border-border bg-elevated px-3.5 py-2.5 text-sm text-foreground placeholder:text-disabled transition-colors focus:border-cyan/60 focus:outline-none focus:ring-2 focus:ring-cyan/15 ${className}`}
    />
  );
}

export function Textarea({
  className = "",
  ...rest
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...rest}
      className={`w-full rounded-xl border border-border bg-elevated px-3.5 py-2.5 text-sm leading-relaxed text-foreground placeholder:text-disabled transition-colors focus:border-cyan/60 focus:outline-none focus:ring-2 focus:ring-cyan/15 ${className}`}
    />
  );
}

const toneText: Record<Tone, string> = {
  muted: "text-muted",
  cyan: "text-cyan",
  critical: "text-critical",
  amber: "text-amber",
};

const toneBadge: Record<Tone, string> = {
  muted: "bg-white/5 text-secondary ring-1 ring-inset ring-white/10",
  cyan: "bg-cyan/10 text-cyan ring-1 ring-inset ring-cyan/25",
  critical: "bg-critical/10 text-critical ring-1 ring-inset ring-critical/30",
  amber: "bg-amber/10 text-amber ring-1 ring-inset ring-amber/25",
};

export function Dot({ tone = "cyan", pulse = false }: { tone?: Tone; pulse?: boolean }) {
  return <span className={`tl-dot ${pulse ? "tl-dot--pulse" : ""} ${toneText[tone]}`} />;
}

export function Badge({
  children,
  tone = "muted",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[0.7rem] font-medium tracking-wide ${toneBadge[tone]}`}
    >
      {children}
    </span>
  );
}
