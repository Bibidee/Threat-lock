"""Seed the gltest Direct-Mode genvm artifact cache with a known-good version.

Why this is needed
------------------
genlayer-test's Direct Mode downloads the GenVM runtime from GitHub. When the
cache is empty it asks GitHub for the *latest* release — but the current "latest"
tag (v0.3.0-rc0) does NOT publish the `genvm-universal.tar.xz` asset, so the
download 404s and every test fails. The last release that ships that asset is
v0.2.16, and it contains the exact runner hash our contract pins in its Depends
header.

This script downloads v0.2.16 into ~/.cache/gltest-direct/ if it isn't already
there. Once cached, the loader prefers the cached version over "latest".

Idempotent: safe to run repeatedly.

Usage:
    .venv\\Scripts\\python.exe scripts\\setup_genvm_cache.py
"""
import sys
import urllib.request
from pathlib import Path

VERSION = "v0.2.16"
URL = f"https://github.com/genlayerlabs/genvm/releases/download/{VERSION}/genvm-universal.tar.xz"


def main() -> int:
    cache = Path.home() / ".cache" / "gltest-direct"
    cache.mkdir(parents=True, exist_ok=True)
    dst = cache / f"genvm-universal-{VERSION}.tar.xz"

    if dst.exists() and dst.stat().st_size > 0:
        print(f"Already cached: {dst} ({dst.stat().st_size // 1024 // 1024} MB)")
        return 0

    print(f"Downloading {URL}")
    print("(~200 MB, one-time)")
    req = urllib.request.Request(URL)
    req.add_header("User-Agent", "threatlock-setup")
    try:
        with urllib.request.urlopen(req, timeout=600) as r, open(dst, "wb") as f:
            f.write(r.read())
    except Exception as e:
        print(f"ERROR: download failed: {e}")
        return 1

    print(f"Saved: {dst} ({dst.stat().st_size // 1024 // 1024} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
