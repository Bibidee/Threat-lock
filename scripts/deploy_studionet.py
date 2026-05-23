"""Deploy the Threat-Lock Intelligent Contract to GenLayer StudioNet.

What it does (idempotent-ish, safe to re-run):
  1. Ensures a repo-root .env exists (copies from .env.example if missing).
  2. Loads or generates the operator private key and saves it to .env.
  3. Connects to StudioNet, initialises the consensus contract.
  4. Funds the operator account from the StudioNet faucet if its balance is low.
  5. Deploys contracts/threat_lock.py and waits for acceptance.
  6. Writes THREATLOCK_CONTRACT_ADDRESS back to .env.

Run (from repo root, project venv):
    .venv\\Scripts\\python.exe scripts\\deploy_studionet.py

The operator account becomes the contract owner/admin, so the backend (which
uses the same key) is authorised to call the control methods.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import genlayer_py as gl
from genlayer_py.types.transactions import TransactionStatus

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / ".env"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
CONTRACT_FILE = REPO_ROOT / "contracts" / "threat_lock.py"

FUND_TARGET_WEI = 1000 * 10**18  # top up to ~1000 GEN if low
FUND_MIN_WEI = 10 * 10**18       # fund when below ~10 GEN


# ----------------------------------------------------------------------
# Tiny .env helpers (no external deps)
# ----------------------------------------------------------------------
def read_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def set_env_var(key: str, value: str) -> None:
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            ENV_FILE.write_text("", encoding="utf-8")
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    out, found = [], False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and stripped.split("=", 1)[0].strip() == key:
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")


def _extract_contract_address(receipt) -> str | None:
    if not isinstance(receipt, dict):
        return None
    for key in ("data", "tx_data_decoded"):
        block = receipt.get(key)
        if isinstance(block, dict):
            addr = block.get("contract_address")
            if addr:
                return addr
    return None


def main() -> int:
    # Windows consoles default to cp1252; force UTF-8 so output never crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    env = read_env()
    rpc = env.get("GENLAYER_RPC_URL") or "https://studio.genlayer.com/api"
    network = (env.get("GENLAYER_NETWORK") or "studionet").lower()
    chain = getattr(gl, network, gl.studionet)

    # 1) operator key
    pk = env.get("GENLAYER_PRIVATE_KEY", "").strip()
    if not pk or pk.startswith("0xYOUR"):
        print("No operator key found — generating a new one…")
        pk = gl.generate_private_key()
        if isinstance(pk, (bytes, bytearray)):
            pk = "0x" + pk.hex()
        set_env_var("GENLAYER_PRIVATE_KEY", pk)
        print(f"  saved GENLAYER_PRIVATE_KEY to {ENV_FILE}")

    account = gl.create_account(pk)
    print(f"Operator address: {account.address}")

    # 2) client + consensus init
    client = gl.create_client(chain=chain, endpoint=rpc, account=account)
    client.initialize_consensus_smart_contract()
    print(f"Connected to {network} ({rpc})")

    # 3) funding
    try:
        bal = int(client.get_balance(account.address))
    except Exception as e:  # noqa: BLE001
        bal = 0
        print(f"  (balance check failed: {e})")
    print(f"Balance: {bal / 10**18:.4f} GEN")
    if bal < FUND_MIN_WEI:
        print("Funding operator from StudioNet faucet…")
        try:
            client.fund_account(account.address, FUND_TARGET_WEI)
            for _ in range(20):
                time.sleep(2)
                bal = int(client.get_balance(account.address))
                if bal >= FUND_MIN_WEI:
                    break
            print(f"  funded. Balance: {bal / 10**18:.4f} GEN")
        except Exception as e:  # noqa: BLE001
            print(f"  WARNING: automatic funding failed: {e}")
            print("  Fund this address from the StudioNet faucet, then re-run.")
            if bal == 0:
                return 2

    # 4) deploy
    if not CONTRACT_FILE.exists():
        print(f"ERROR: contract not found at {CONTRACT_FILE}")
        return 1
    code = CONTRACT_FILE.read_text(encoding="utf-8")
    print("Deploying contracts/threat_lock.py …")
    tx_id = client.deploy_contract(code=code, account=account, args=[])
    print(f"  deploy tx: {tx_id}")
    print("  waiting for acceptance (this can take a minute)…")
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=tx_id,
        status=TransactionStatus.ACCEPTED,
        interval=3000,
        retries=60,
    )

    address = _extract_contract_address(receipt)
    if not address:
        print("ERROR: could not find contract address in receipt.")
        print(f"  receipt keys: {list(receipt.keys()) if isinstance(receipt, dict) else type(receipt)}")
        return 1

    set_env_var("THREATLOCK_CONTRACT_ADDRESS", address)
    print("\n=========================================")
    print("  DEPLOYED [OK]")
    print(f"  Contract: {address}")
    print(f"  Owner:    {account.address}")
    print(f"  Saved THREATLOCK_CONTRACT_ADDRESS to {ENV_FILE}")
    print(f"  Explorer: https://explorer-studio.genlayer.com/contracts/{address}")
    print("=========================================")
    print("\nNext: restart the backend so it picks up the address.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
