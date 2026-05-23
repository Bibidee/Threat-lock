"""Edit a key in the root .env without a text editor.

Adds the key if missing, replaces it if present. Values containing spaces are
quoted automatically (needed for the Fly token).

Usage:
  # Hidden prompt (best for tokens/secrets -- paste at the prompt, nothing echoes
  # and nothing is stored in your shell history):
  python scripts/set_env.py FLY_API_TOKEN
  python scripts/set_env.py VERCEL_TOKEN

  # Inline value (fine for non-secret config; note: this DOES go in shell history):
  python scripts/set_env.py FLY_APP threatlock-api-bibidee
"""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / ".env"


def set_key(key: str, value: str) -> None:
    needs_quotes = (" " in value) and not (value.startswith('"') and value.endswith('"'))
    stored = f'"{value}"' if needs_quotes else value
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    out, seen = [], False
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s and s.split("=", 1)[0].strip() == key:
            out.append(f"{key}={stored}")
            seen = True
        else:
            out.append(line)
    if not seen:
        out.append(f"{key}={stored}")
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/set_env.py KEY [VALUE]")
        return 1
    key = sys.argv[1]
    if len(sys.argv) >= 3:
        value = " ".join(sys.argv[2:]).strip()
    else:
        value = getpass.getpass(f"Paste value for {key} (hidden, then Enter): ").strip()
    if not value:
        print("No value entered. Nothing changed.")
        return 1
    set_key(key, value)
    print(f"OK: {key} saved to .env ({len(value)} chars).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
