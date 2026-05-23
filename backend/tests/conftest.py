"""Test isolation for backend tests.

Forces local GenLayer mode + in-memory Firebase so tests NEVER touch the live
StudioNet contract or a real Firebase project. Env is set at import time, and
pytest_configure additionally clears cached settings/singletons in case anything
imported app.config before this ran.
"""
import os

os.environ["GENLAYER_MODE"] = "local"
os.environ["GENLAYER_CONTRACT_ADDRESS"] = ""
os.environ["GENLAYER_PRIVATE_KEY"] = ""
os.environ["FIREBASE_PROJECT_ID"] = ""
os.environ["FIREBASE_CLIENT_EMAIL"] = ""
os.environ["FIREBASE_PRIVATE_KEY"] = ""
os.environ["FIREBASE_SERVICE_ACCOUNT"] = "firebase/__none__.json"
os.environ["ADMIN_WALLET_ADDRESS"] = "0x00000000000000000000000000000000000ADMIN"
os.environ["BACKEND_API_KEY"] = ""  # no shared key in tests (exercise per-key enforcement)
os.environ["AEGIS_VAULT_ADDRESS"] = ""  # vault uses local fallback in tests
os.environ["APP_ENV"] = "test"


def pytest_configure(config):  # noqa: ARG001
    import app.config as cfg
    cfg.get_settings.cache_clear()

    import app.integrations.genlayer_client as gc
    gc._client = None
    import app.integrations.firebase_client as fc
    fc._client = None
    import app.repositories.firebase_repository as repo
    repo._repo = None

    # sanity: fail loudly rather than ever touching the live chain
    assert cfg.get_settings().genlayer_mode == "local", "test isolation failed: not local mode"
    assert not cfg.get_settings().genlayer_real, "test isolation failed: genlayer_real is True"
