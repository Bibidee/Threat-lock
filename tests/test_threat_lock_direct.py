"""Direct Mode unit tests for the Threat-Lock Intelligent Contract.

Direct Mode runs the contract's Python in-memory (no Docker, no network), so
these tests execute in milliseconds. Run them with:

    .venv\\Scripts\\python.exe -m pytest tests/test_threat_lock_direct.py -v

Fixtures provided by the `genlayer-test` pytest plugin:
    direct_deploy  -> deploy a contract file in-memory, returns the instance
    direct_vm      -> VM context + cheatcodes (prank, expect_revert, mock_llm)
    direct_owner   -> default deployer / sender address
    direct_alice   -> a second test address (not an admin by default)
    direct_bob     -> a third test address
"""

CONTRACT = "contracts/threat_lock.py"

# A fixed epoch-seconds value used wherever the contract wants `reported_at`.
TS = 1_716_200_000


def _status(contract) -> dict:
    return contract.get_status()


def _addr(a):
    """Coerce a Direct-Mode address fixture (raw bytes) into a GenLayer Address.

    On the real network, calldata decoding turns address arguments into Address
    objects automatically. Direct Mode passes the raw bytes through, so for
    methods that take an Address argument we wrap them here. (The genlayer SDK is
    importable once a contract has been deployed in the test.)
    """
    from genlayer import Address

    return a if isinstance(a, Address) else Address(a)


# --------------------------------------------------------------------------
# Deployment / initial state
# --------------------------------------------------------------------------
def test_initial_state(direct_deploy):
    c = direct_deploy(CONTRACT)
    s = _status(c)
    assert bool(s["paused"]) is False
    assert int(s["threat_score"]) == 0
    assert int(s["pause_threshold"]) == 75
    assert int(s["event_count"]) == 0
    assert c.is_paused() is False


# --------------------------------------------------------------------------
# Deterministic threat reporting + auto-freeze
# --------------------------------------------------------------------------
def test_report_below_threshold_does_not_pause(direct_deploy):
    c = direct_deploy(CONTRACT)
    c.report_threat(50, "minor volume blip", "monitor", TS)
    s = _status(c)
    assert int(s["threat_score"]) == 50
    assert bool(s["paused"]) is False
    assert int(s["event_count"]) == 1  # THREAT_REPORTED


def test_report_at_or_above_threshold_auto_freezes(direct_deploy):
    c = direct_deploy(CONTRACT)
    c.report_threat(90, "massive outflow detected", "monitor", TS)
    s = _status(c)
    assert int(s["threat_score"]) == 90
    assert bool(s["paused"]) is True
    # THREAT_REPORTED + AUTO_PAUSED
    assert int(s["event_count"]) == 2


# --------------------------------------------------------------------------
# Manual pause / recovery
# --------------------------------------------------------------------------
def test_manual_pause_and_unpause(direct_deploy):
    c = direct_deploy(CONTRACT)
    c.emergency_pause("operator pulled the switch", TS)
    assert c.is_paused() is True
    c.unpause("threat cleared, resuming", TS)
    s = _status(c)
    assert bool(s["paused"]) is False
    assert int(s["threat_score"]) == 0


# --------------------------------------------------------------------------
# Admin authorization
# --------------------------------------------------------------------------
def test_non_admin_cannot_report(direct_deploy, direct_vm, direct_bob):
    c = direct_deploy(CONTRACT)
    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("admin only"):
            c.report_threat(90, "spoofed", "attacker", TS)


def test_owner_can_grant_admin(direct_deploy, direct_vm, direct_alice):
    c = direct_deploy(CONTRACT)
    alice = _addr(direct_alice)
    assert c.is_admin(alice) is False
    c.add_admin(alice, TS)
    assert c.is_admin(alice) is True
    # Now alice (a fresh admin) can report a threat.
    with direct_vm.prank(direct_alice):
        c.report_threat(40, "alice reporting", "monitor", TS)
    assert int(_status(c)["threat_score"]) == 40


def test_only_owner_removes_admin(direct_deploy, direct_vm, direct_alice, direct_bob):
    c = direct_deploy(CONTRACT)
    alice = _addr(direct_alice)
    bob = _addr(direct_bob)
    c.add_admin(alice, TS)
    c.add_admin(bob, TS)
    # bob is an admin but NOT the owner -> cannot remove alice
    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("only owner"):
            c.remove_admin(alice, TS)
    # owner can
    c.remove_admin(alice, TS)
    assert c.is_admin(alice) is False


# --------------------------------------------------------------------------
# Threshold tuning
# --------------------------------------------------------------------------
def test_set_threshold_changes_autofreeze_point(direct_deploy):
    c = direct_deploy(CONTRACT)
    c.set_threshold(40, TS)
    assert int(_status(c)["pause_threshold"]) == 40
    c.report_threat(45, "now above the lowered bar", "monitor", TS)
    assert c.is_paused() is True


# --------------------------------------------------------------------------
# AI anomaly verification (LLM path, mocked)
# --------------------------------------------------------------------------
def test_ai_verify_confirms_and_freezes(direct_deploy, direct_vm):
    c = direct_deploy(CONTRACT)
    direct_vm.mock_llm(
        r".*",
        '{"is_threat": true, "confidence": 92, "reasoning": "reentrancy drain in progress"}',
    )
    c.verify_threat("Anomalous repeated withdraw() calls draining the pool.", TS)
    s = _status(c)
    assert int(s["threat_score"]) == 92
    assert bool(s["paused"]) is True


def test_ai_verify_low_confidence_does_not_freeze(direct_deploy, direct_vm):
    c = direct_deploy(CONTRACT)
    direct_vm.mock_llm(
        r".*",
        '{"is_threat": true, "confidence": 30, "reasoning": "possibly benign arbitrage"}',
    )
    c.verify_threat("Slightly elevated swap volume on one pair.", TS)
    s = _status(c)
    assert int(s["threat_score"]) == 30
    assert bool(s["paused"]) is False


def test_ai_verify_not_a_threat(direct_deploy, direct_vm):
    c = direct_deploy(CONTRACT)
    direct_vm.mock_llm(
        r".*",
        '{"is_threat": false, "confidence": 95, "reasoning": "normal governance activity"}',
    )
    c.verify_threat("Routine governance proposal executed.", TS)
    # High confidence, but not a threat -> must NOT pause.
    assert c.is_paused() is False
