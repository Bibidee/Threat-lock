# Aegis Vault

Aegis Vault is the **protected demo protocol** for Threat-Lock. It is a GenLayer
Intelligent Contract (not a website) that holds value and **blocks withdrawals
on-chain while it is frozen**. Threat-Lock holds the *guardian* role and freezes
the vault the moment its AI judge confirms an attack — proving the system does
more than alert: it stops the bleed at the contract level.

It surfaces in the existing dashboard as the **"Protected Vault (Aegis)"** card.
There is no separate site.

## What it is made of

| Layer | File | Role |
|---|---|---|
| Contract | `contracts/aegis_vault.py` | On-chain vault: deposit/withdraw/freeze |
| Integration | `backend/app/integrations/vault_client.py` | Reads/writes the contract (or in-memory in local mode) |
| Service | `backend/app/services/vault_service.py` | `status` / `deposit` / `withdraw` / `sync_freeze` |
| Routes | `backend/app/routes/vault.py` | `GET /api/vault/status`, `POST /api/vault/deposit`, `POST /api/vault/withdraw` |
| UI | `frontend/src/components/dashboard/ProtectedVault.tsx` | The dashboard card |
| Hook | `frontend/src/hooks/useVault.ts` | Polls status, calls deposit/withdraw |

## On-chain contract

Deployed to StudioNet at **`0xC4aA52157b2A1d39f534ae6CaCB37De0bAcf4E1b`**
(stored as `AEGIS_VAULT_ADDRESS` in `.env`).

**State**

| Field | Type | Meaning |
|---|---|---|
| `admin` | `Address` | Deployer; can freeze/unfreeze and assign guardian |
| `guardian` | `Address` | Threat-Lock's role; can freeze/unfreeze |
| `frozen` | `bool` | When true, all withdrawals revert |
| `freeze_reason` | `str` | Why it was frozen / recovery note |
| `total_locked` | `u256` | Total value locked (TVL) |

**Methods**

- `deposit(amount)` — adds to TVL.
- `withdraw(amount)` — `assert not self.frozen` → reverts with `VAULT_FROZEN_BY_THREATLOCK` while frozen; also checks TVL.
- `freeze(reason)` / `unfreeze(note)` — gated to `admin` **or** `guardian`.
- `set_guardian(addr)` — admin assigns the guardian (so Threat-Lock can freeze).
- views: `is_frozen`, `total_value_locked`, `get_freeze_reason`, `get_admin`, `get_guardian`.

The protection is enforced **by the chain**, not by the UI or backend — a frozen
vault rejects withdrawals even if someone calls the contract directly.

## How Threat-Lock controls it

The backend signs as the operator key (`GENLAYER_PRIVATE_KEY`), which is the
vault's guardian. Freeze/unfreeze are wired into the incident lifecycle and are
**best-effort and no-op when no vault is configured** (`sync_freeze` never raises
into the pipeline):

| Event | Hook | Effect on vault |
|---|---|---|
| Critical threat auto-pauses the system | `threat_service.process` → `vault_service.sync_freeze(True, …)` | **Freezes** |
| Admin manual pause | `admin_service.manual_pause` → `sync_freeze(True, …)` | **Freezes** |
| Admin unpause / recovery | `admin_service.unpause` → `sync_freeze(False, …)` | **Unfreezes** |

## Local vs real mode

- `GENLAYER_MODE=real` + `AEGIS_VAULT_ADDRESS` set → talks to the live StudioNet
  contract (`vault_enabled == True`).
- `GENLAYER_MODE=local` (or no address) → an in-memory vault so the dashboard and
  tests work without a chain. Backend tests run in this mode with the address
  blanked, so `sync_freeze` is a no-op.

## API quick reference

```http
GET  /api/vault/status
  -> { configured, frozen, freeze_reason, total_locked, address }

POST /api/vault/deposit   { "amount": 100 }   -> { result: "DEPOSITED", tx_hash }
POST /api/vault/withdraw  { "amount": 100 }   -> { result: "WITHDRAWN", tx_hash }
     # 409 "Withdrawals are frozen by Threat-Lock." when frozen
```

## Redeploying

```powershell
.\.venv\Scripts\python.exe scripts\deploy_aegis_vault.py
```
Deploys the contract, runs the on-chain proof
(deposit → withdraw → freeze → withdraw blocked → unfreeze → withdraw), and saves
the new `AEGIS_VAULT_ADDRESS` to `.env`.

### GenVM registration gotchas (learned the hard way)
Two things silently prevent the contract from registering on StudioNet (it
deploys but never becomes queryable):
1. **Binding `gl.message.sender_address` to a local variable** (`s = gl.message.sender_address`).
   Use it inline: `gl.message.sender_address == self.admin or gl.message.sender_address == self.guardian`.
2. **Extra descriptive comment lines** near the top of the file. Keep only the
   required `# { "Depends": "py-genlayer:…" }` header above `from genlayer import *`.
