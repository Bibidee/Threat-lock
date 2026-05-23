"""One-shot, non-interactive deploy for Threat-Lock.

  Backend  -> Fly.io   (FastAPI server, holds the admin key)
  Frontend -> Vercel   (Next.js dashboard)

Everything is driven from the root .env. Order matters: the backend goes up
first so the frontend can be built against its public URL, then the backend's
CORS origin is pointed at the deployed frontend.

Prereqs (install once, then never log in -- tokens come from .env):
  * Fly CLI:    https://fly.io/docs/flyctl/install/      (`flyctl` or `fly`)
  * Vercel CLI: `npm i -g vercel`  (or it falls back to `npx vercel`)
  * Node/npm available on PATH (Vercel CLI needs it).

Required in .env:
  FLY_API_TOKEN=...        # flyctl auth token  (`flyctl tokens create org`)
  VERCEL_TOKEN=...         # https://vercel.com/account/tokens
Optional in .env (sensible defaults shown):
  FLY_APP=threatlock-api
  FLY_REGION=iad
  FLY_ORG=personal
  VERCEL_PROJECT=threatlock-dashboard

Usage:
  .venv\\Scripts\\python.exe scripts\\deploy.py            # deploy both
  .venv\\Scripts\\python.exe scripts\\deploy.py --backend   # backend only
  .venv\\Scripts\\python.exe scripts\\deploy.py --frontend  # frontend only
  .venv\\Scripts\\python.exe scripts\\deploy.py --dry-run    # print plan, do nothing
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENV = REPO / ".env"
FLY_TOML = REPO / "fly.toml"
FRONTEND = REPO / "frontend"

# Backend env keys that must NOT be shipped to Fly as app secrets.
DENY_PREFIXES = ("FLY_", "VERCEL_", "NEXT_PUBLIC_")
DENY_KEYS = {"FIREBASE_SERVICE_ACCOUNT", "FRONTEND_ORIGIN", "BACKEND_HOST", "BACKEND_PORT"}

# Frontend (build-time) env vars, sourced from .env with fallbacks computed below.
FRONTEND_KEYS = (
    "NEXT_PUBLIC_API_BASE_URL",
    "NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS",
    "NEXT_PUBLIC_ADMIN_WALLET_ADDRESS",
)

DRY = False


# ---------------------------------------------------------------- helpers ----
def load_env() -> dict:
    d: dict[str, str] = {}
    if not ENV.exists():
        die(f"No .env at {ENV}")
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        d[k.strip()] = v
    return d


def die(msg: str) -> None:
    print(f"\nERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def step(msg: str) -> None:
    print(f"\n=== {msg} ===")


def run(cmd: list[str], *, env: dict | None = None, stdin: str | None = None,
        capture: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    print(f"$ {_redact_cmd(cmd)}")
    if DRY:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    full_env = {**os.environ, **(env or {})}
    res = subprocess.run(
        cmd, env=full_env, input=stdin, text=True,
        capture_output=capture,
    )
    if capture and res.stdout:
        print(res.stdout)
    if check and res.returncode != 0:
        if capture and res.stderr:
            print(res.stderr, file=sys.stderr)
        die(f"command failed ({res.returncode}): {_redact_cmd(cmd)}")
    return res


def _redact_cmd(cmd: list[str]) -> str:
    # hide the value that follows --token (the only secret passed as an arg)
    out, redact_next = [], False
    for c in cmd:
        if redact_next:
            out.append(c[:4] + "***" if len(c) > 6 else "***")
            redact_next = False
        else:
            out.append(c)
            redact_next = c == "--token"
    return " ".join(out)


def find_fly() -> list[str]:
    for name in ("flyctl", "fly"):
        p = shutil.which(name)
        if p:
            return [p]
    if DRY:
        return ["flyctl"]
    die("Fly CLI not found. Install: https://fly.io/docs/flyctl/install/")
    return []


def find_vercel() -> list[str]:
    p = shutil.which("vercel")
    if p:
        return [p]
    npx = shutil.which("npx")
    if npx:
        return [npx, "--yes", "vercel"]
    if DRY:
        return ["vercel"]
    die("Vercel CLI not found. Install: npm i -g vercel  (or install Node for npx)")
    return []


# --------------------------------------------------------------- backend ----
def _firebase_inline(env: dict) -> list[str]:
    """Return FIREBASE_* secret lines for Fly.

    If .env already supplies the inline creds, ship those. Otherwise read the
    service-account JSON and flatten the private key to a single line.
    """
    import json
    if env.get("FIREBASE_PRIVATE_KEY") and env.get("FIREBASE_CLIENT_EMAIL"):
        return []  # already shipped by the main loop from .env
    path = env.get("FIREBASE_SERVICE_ACCOUNT") or "firebase/serviceAccountKey.json"
    p = Path(path)
    if not p.is_absolute():
        p = REPO / p
    if not p.exists():
        print(f"  WARNING: no Firebase service account at {p};")
        print("           backend will run with the in-memory store (data not persisted).")
        return []
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"  WARNING: could not read {p}: {e}; using in-memory store.")
        return []
    pk = (d.get("private_key") or "").replace("\r\n", "\n").replace("\n", "\\n")
    print("  shipping Firebase creds inline (Firestore persistence enabled)")
    return [
        f"FIREBASE_PROJECT_ID={d.get('project_id', '')}",
        f"FIREBASE_CLIENT_EMAIL={d.get('client_email', '')}",
        f"FIREBASE_PRIVATE_KEY={pk}",
    ]


def patch_fly_toml(app: str, region: str) -> None:
    text = FLY_TOML.read_text(encoding="utf-8")
    text = re.sub(r'(?m)^app\s*=.*$', f'app = "{app}"', text, count=1)
    text = re.sub(r'(?m)^primary_region\s*=.*$', f'primary_region = "{region}"', text, count=1)
    if not DRY:
        FLY_TOML.write_text(text, encoding="utf-8")
    print(f"  fly.toml -> app={app} region={region}")


def deploy_backend(env: dict) -> str:
    token = env.get("FLY_API_TOKEN")
    if not token and not DRY:
        die("FLY_API_TOKEN missing in .env")
    token = token or "DRYRUN"
    app = env.get("FLY_APP", "threatlock-api")
    region = env.get("FLY_REGION", "iad")
    org = env.get("FLY_ORG", "personal")
    fly = find_fly()
    fly_env = {"FLY_API_TOKEN": token}

    step(f"Backend -> Fly.io  (app={app}, region={region})")

    # A Fly *deploy/org token* can deploy + set secrets on an EXISTING app, but
    # usually cannot list orgs, list apps, or create apps. So we never call those
    # here -- the app must be created once manually (your logged-in CLI):
    #     flyctl apps create <name> -o personal
    if not DRY and ("testtoken" in token or not token.startswith("FlyV1")):
        die("FLY_API_TOKEN in .env is not a real Fly token.\n"
            "  1) flyctl tokens create org -o personal\n"
            "  2) .venv\\Scripts\\python.exe scripts\\set_env.py FLY_API_TOKEN  (paste at prompt)")

    patch_fly_toml(app, region)

    # build & ship the backend secrets (everything in .env except deploy/frontend)
    secret_lines = []
    for k, v in env.items():
        if k.startswith(DENY_PREFIXES) or k in DENY_KEYS:
            continue
        secret_lines.append(f"{k}={v}")
    # neutralise the file-based firebase path so it uses the 3 FIREBASE_* fields
    secret_lines.append("FIREBASE_SERVICE_ACCOUNT=")
    secret_lines.append("APP_ENV=production")
    # Fly has no service-account file -> ship Firebase creds inline. If the 3
    # FIREBASE_* fields aren't already in .env, derive them from the JSON file
    # (private key flattened to one line; the backend restores the newlines).
    for line in _firebase_inline(env):
        secret_lines.append(line)
    print(f"  importing {len(secret_lines)} secrets to Fly (values hidden)")
    sec = run(fly + ["secrets", "import", "--app", app, "--stage"], env=fly_env,
              stdin="\n".join(secret_lines) + "\n", capture=True, check=False)
    if not DRY and sec.returncode != 0:
        blob = ((sec.stdout or "") + (sec.stderr or "")).strip()
        low = blob.lower()
        if "could not find app" in low or "not found" in low:
            die(f"Fly app '{app}' does not exist. Create it once with your login, then re-run:\n"
                f"  flyctl apps create {app} -o personal\n"
                f"  .venv\\Scripts\\python.exe scripts\\deploy.py\n\n"
                f"(Also confirm FLY_APP in .env matches the app you created.)")
        if "auth" in low or "authenticated" in low or "unauthorized" in low:
            die("Fly rejected FLY_API_TOKEN. Create a fresh org token and store it:\n"
                "  flyctl tokens create org -o personal\n"
                "  .venv\\Scripts\\python.exe scripts\\set_env.py FLY_API_TOKEN  (paste at prompt)")
        die(f"Setting Fly secrets failed:\n{blob}")

    # build + deploy from the Dockerfile (remote builder, no local Docker needed)
    run(fly + ["deploy", "--app", app, "--config", str(FLY_TOML),
               "--remote-only", "--yes"], env=fly_env)

    url = f"https://{app}.fly.dev"
    print(f"  backend live: {url}")
    return url


# -------------------------------------------------------------- frontend ----
def vercel_set_env(vercel: list[str], token: str, name: str, value: str) -> None:
    # remove then add so re-runs are idempotent. --cwd must point at the linked
    # frontend dir (the repo root is NOT a linked Vercel project).
    cwd = ["--cwd", str(FRONTEND)]
    run(vercel + ["env", "rm", name, "production", "--yes", "--token", token] + cwd,
        capture=True, check=False)
    run(vercel + ["env", "add", name, "production", "--token", token] + cwd, stdin=value)


def deploy_frontend(env: dict, backend_url: str | None) -> str:
    token = env.get("VERCEL_TOKEN")
    if not token and not DRY:
        die("VERCEL_TOKEN missing in .env")
    token = token or "DRYRUN"
    project = env.get("VERCEL_PROJECT", "threatlock-dashboard")
    vercel = find_vercel()

    step(f"Frontend -> Vercel  (project={project})")

    # link (or create) the project non-interactively, scoped to the frontend dir
    run(vercel + ["link", "--yes", "--project", project, "--token", token,
                  "--cwd", str(FRONTEND)], check=False)

    # resolve build-time public env vars (NEXT_PUBLIC_*).
    # priority: this run's backend URL > .env override > derived from FLY_APP.
    derived = f"https://{env['FLY_APP']}.fly.dev" if env.get("FLY_APP") else ""
    api_base = backend_url or env.get("NEXT_PUBLIC_API_BASE_URL") or derived
    values = {
        "NEXT_PUBLIC_API_BASE_URL": api_base,
        "NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS":
            env.get("NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS")
            or env.get("GENLAYER_CONTRACT_ADDRESS", ""),
        "NEXT_PUBLIC_ADMIN_WALLET_ADDRESS":
            env.get("NEXT_PUBLIC_ADMIN_WALLET_ADDRESS")
            or env.get("ADMIN_WALLET_ADDRESS", ""),
    }
    if not values["NEXT_PUBLIC_API_BASE_URL"]:
        die("No API base URL: deploy the backend first, set NEXT_PUBLIC_API_BASE_URL, "
            "or run without --frontend-only.")
    for name, val in values.items():
        print(f"  set {name} = {val}")
        vercel_set_env(vercel, token, name, val)

    # production build + deploy (uses the env vars we just set)
    res = run(vercel + ["deploy", "--prod", "--yes", "--token", token,
                        "--cwd", str(FRONTEND)], capture=True)
    out = (res.stdout or "").strip().splitlines()
    url = next((l.strip() for l in reversed(out) if l.strip().startswith("https://")),
               f"https://{project}.vercel.app")
    print(f"  frontend live: {url}")
    return url


# ------------------------------------------------------------------ main ----
def main() -> int:
    global DRY
    ap = argparse.ArgumentParser(description="Deploy Threat-Lock (Fly + Vercel)")
    ap.add_argument("--backend", action="store_true", help="deploy backend only")
    ap.add_argument("--frontend", action="store_true", help="deploy frontend only")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    args = ap.parse_args()
    DRY = args.dry_run
    do_backend = args.backend or not args.frontend
    do_frontend = args.frontend or not args.backend

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    env = load_env()
    backend_url = None
    frontend_url = None

    if do_backend:
        backend_url = deploy_backend(env)

    if do_frontend:
        frontend_url = deploy_frontend(env, backend_url)

    # point backend CORS at the deployed frontend (only if we have both this run)
    if do_backend and frontend_url:
        token = env["FLY_API_TOKEN"]
        app = env.get("FLY_APP", "threatlock-api")
        step("Wiring CORS: backend FRONTEND_ORIGIN -> frontend URL")
        run(find_fly() + ["secrets", "set", f"FRONTEND_ORIGIN={frontend_url}",
                          "--app", app], env={"FLY_API_TOKEN": token})

    step("DONE")
    if backend_url:
        print(f"  Backend : {backend_url}   (health: {backend_url}/api/health)")
    if frontend_url:
        print(f"  Frontend: {frontend_url}")
    print("\nVerify:")
    if backend_url:
        print(f"  curl {backend_url}/api/health")
        print(f"  curl {backend_url}/api/vault/status   # expect configured:true")
    if frontend_url:
        print(f"  open  {frontend_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
