"""Patch genlayer-test's Direct Mode loader to work on Windows.

Problem
-------
genlayer-test <= 0.29.2 sets up the GenVM message by writing it to a temp file,
binding that file to stdin via os.dup2(fd, 0), and then immediately calling
os.unlink(path) in a finally block. On POSIX you can unlink an open file; on
Windows you cannot, so every Direct Mode test crashes with:

    PermissionError: [WinError 32] The process cannot access the file
    because it is being used by another process

Fix
---
Make the unlink best-effort: try to delete now, and if Windows refuses because
the file is still open as stdin, defer deletion to interpreter exit. This is a
no-op behavioural change on POSIX.

This script edits the installed package inside the venv. It is idempotent: run
it again any time you recreate the venv or reinstall genlayer-test.

Usage:
    .venv\\Scripts\\python.exe scripts\\patch_gltest_windows.py
"""
import sys
from pathlib import Path

MARKER = "_gl_safe_unlink"

HELPER = '''
def _gl_safe_unlink(path):
    """Best-effort temp-file removal (Windows can't unlink an open stdin fd)."""
    import os
    import atexit
    try:
        os.unlink(path)
    except OSError:
        def _later(p=path):
            try:
                os.unlink(p)
            except OSError:
                pass
        atexit.register(_later)


'''

OLD_FINALLY = "    finally:\n        os.close(fd)\n        os.unlink(path)\n"
NEW_FINALLY = "    finally:\n        os.close(fd)\n        _gl_safe_unlink(path)\n"


def find_loader() -> Path:
    import gltest.direct.loader as loader  # noqa: F401

    return Path(loader.__file__)


def main() -> int:
    try:
        loader_path = find_loader()
    except Exception as e:  # pragma: no cover
        print(f"ERROR: could not locate gltest loader: {e}")
        return 1

    text = loader_path.read_text(encoding="utf-8")

    if MARKER in text:
        print(f"Already patched: {loader_path}")
        return 0

    if OLD_FINALLY not in text:
        print("ERROR: expected code block not found — gltest internals may have")
        print(f"changed. Inspect manually: {loader_path}")
        return 2

    # Insert the helper just before the first top-level `def _load_module`.
    anchor = "def _load_module("
    if anchor in text:
        text = text.replace(anchor, HELPER.lstrip("\n") + anchor, 1)
    else:
        text = HELPER + text  # fallback: prepend

    text = text.replace(OLD_FINALLY, NEW_FINALLY, 1)
    loader_path.write_text(text, encoding="utf-8")
    print(f"Patched OK: {loader_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
