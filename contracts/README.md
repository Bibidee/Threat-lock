# Threat-Lock — Intelligent Contract

`threat_lock.py` is the on-chain core: the emergency **pause** state machine plus
threat scoring, AI anomaly verification, admin control, auto-freeze, recovery,
and an append-only audit log.

## State

| Field             | Type                      | Meaning                                  |
|-------------------|---------------------------|------------------------------------------|
| `owner`           | `Address`                 | Deployer; super-admin, cannot be removed |
| `paused`          | `bool`                    | The emergency kill switch                |
| `threat_score`    | `u256`                    | Latest threat score (0–100)              |
| `pause_threshold` | `u256`                    | Auto-freeze when score ≥ this            |
| `last_reason`     | `str`                     | Latest reason string                     |
| `event_count`     | `u256`                    | Number of audit-log entries              |
| `admins`          | `TreeMap[Address, bool]`  | Authorized admins                        |
| `events`          | `DynArray[ThreatEvent]`   | Append-only audit log                    |

`ThreatEvent = { kind, score, reason, actor, timestamp }`.

## Write methods (state-changing, admin-gated)

| Method | Args | Purpose |
|--------|------|---------|
| `report_threat` | `score:u256, reason:str, source:str, reported_at:u256` | Deterministic path: backend reports a precomputed score; auto-freezes if ≥ threshold |
| `verify_threat` | `evidence:str, reported_at:u256` | **AI path**: LLM judges if evidence is a real exploit (leader/validator consensus); auto-freezes if confirmed & confident |
| `emergency_pause` | `reason:str, reported_at:u256` | Manual kill switch |
| `unpause` | `reason:str, reported_at:u256` | Recovery: lift pause, reset score |
| `set_threshold` | `new_threshold:u256, reported_at:u256` | Tune auto-freeze threshold |
| `add_admin` | `addr:Address, reported_at:u256` | Grant admin (any admin) |
| `remove_admin` | `addr:Address, reported_at:u256` | Revoke admin (owner only) |

> `reported_at` is a caller-supplied epoch-seconds timestamp. We pass it in (rather
> than read chain time) to keep the log deterministic across validators.

## View methods (read-only, free)

| Method | Returns |
|--------|---------|
| `get_status()` | `{paused, threat_score, pause_threshold, event_count, last_reason, owner}` |
| `is_paused()` | `bool` |
| `is_admin(addr)` | `bool` |
| `get_recent_events(limit)` | last `limit` audit-log entries |

## How threat detection flows

```
monitoring worker  ─ objective signal ─►  report_threat(score,…)  ─┐
                                                                   ├─► score ≥ threshold? → AUTO_PAUSED
monitoring worker  ─ fuzzy evidence  ─►  verify_threat(evidence) ─┘     (LLM-confirmed for the AI path)
admin / dashboard  ─────────────────►  emergency_pause / unpause
```

## Consensus design (why it's trustworthy)

- The AI path uses GenLayer's **Equivalence Principle** via
  `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)`. The leader asks the LLM for a
  structured verdict `{is_threat, confidence, reasoning}`; validators independently
  re-run and accept only if the **boolean decision matches** and confidence is within
  tolerance. Reasoning text may differ between LLMs — that's expected and ignored.
- All write methods call `_require_admin()`; `remove_admin` is owner-only.

## Depends header

The first line pins the GenVM standard-library version. Keep it — deployment fails
without it.
