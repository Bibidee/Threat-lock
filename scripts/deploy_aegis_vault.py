"""Deploy the Aegis Vault demo protocol to StudioNet, then prove Threat-Lock
protection on-chain: deposit -> withdraw works -> freeze -> withdraw BLOCKED ->
unfreeze -> withdraw works. Saves AEGIS_VAULT_ADDRESS to .env.

Run: .venv\\Scripts\\python.exe scripts\\deploy_aegis_vault.py
"""
import sys
import time
from pathlib import Path

import genlayer_py as gl
from genlayer_py.types.transactions import TransactionStatus

REPO = Path(__file__).resolve().parents[1]
ENV = REPO / ".env"


def env() -> dict:
    d = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def set_env(key: str, val: str) -> None:
    lines = ENV.read_text(encoding="utf-8").splitlines()
    out, seen = [], False
    for l in lines:
        if l.strip() and not l.strip().startswith("#") and l.split("=", 1)[0].strip() == key:
            out.append(f"{key}={val}"); seen = True
        else:
            out.append(l)
    if not seen:
        out.append(f"{key}={val}")
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    e = env()
    acct = gl.create_account(e["GENLAYER_PRIVATE_KEY"])
    c = gl.create_client(chain=gl.studionet, endpoint=e.get("GENLAYER_RPC_URL"), account=acct)
    c.initialize_consensus_smart_contract()
    code = (REPO / "contracts" / "aegis_vault.py").read_text(encoding="utf-8")

    print("Deploying AegisVault...")
    tx = c.deploy_contract(code=code, account=acct, args=[])
    c.wait_for_transaction_receipt(transaction_hash=tx, status=TransactionStatus.FINALIZED,
                                   interval=4000, retries=60)
    # the deployed address is in the receipt data
    rec = c.get_transaction(tx)
    addr = (rec.get("data") or {}).get("contract_address")
    print("AegisVault address:", addr)

    # poll until the contract is queryable (StudioNet registration can lag)
    ready = False
    for i in range(40):
        try:
            c.read_contract(address=addr, function_name="is_frozen")
            ready = True
            break
        except Exception:
            time.sleep(6)
    if not ready:
        print("ERROR: contract never became queryable")
        return 1
    set_env("AEGIS_VAULT_ADDRESS", addr)
    print("Saved AEGIS_VAULT_ADDRESS")

    def write(fn, args):
        t = c.write_contract(address=addr, function_name=fn, account=acct, args=args)
        try:
            c.wait_for_transaction_receipt(transaction_hash=t, status=TransactionStatus.ACCEPTED,
                                           interval=4000, retries=50)
        except Exception as ex:
            print(f"   (tx note for {fn}: {str(ex)[:60]})")

    def tvl():
        return int(c.read_contract(address=addr, function_name="total_value_locked"))

    def frozen():
        return c.read_contract(address=addr, function_name="is_frozen")

    print("\n--- PROTECTION DEMO ---")
    write("deposit", [1000]); print("deposit 1000 -> tvl", tvl())
    write("withdraw", [100]); print("withdraw 100 (open) -> tvl", tvl())
    write("freeze", ["Threat-Lock: confirmed active exploit"]); print("FREEZE -> frozen", frozen())
    before = tvl()
    write("withdraw", [100]); after = tvl()
    print(f"withdraw 100 while FROZEN -> tvl {after} ({'BLOCKED' if after == before else 'LEAKED!'})")
    write("unfreeze", ["recovered after review"]); print("UNFREEZE -> frozen", frozen())
    write("withdraw", [100]); print("withdraw 100 (open again) -> tvl", tvl())
    print("--- DONE ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
