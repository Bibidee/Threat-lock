"""Strip HTML from a saved GenLayer doc dump and print readable text.

Usage:
    python scripts/clean_doc.py <path-to-saved-tool-result.txt>

The GenLayer docs MCP returns full HTML pages that are too large to read
inline. This helper strips scripts/styles/tags and collapses whitespace so we
can read the actual prose + code examples. Windows-safe stdout encoding.
"""
import sys
import re
import html


def clean(path: str) -> str:
    text = open(path, encoding="utf-8", errors="replace").read()
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python scripts/clean_doc.py <file>")
        sys.exit(1)
    out = clean(sys.argv[1])
    # Force UTF-8 stdout so unicode arrows etc. don't crash on Windows cp1252.
    sys.stdout.reconfigure(encoding="utf-8")
    print(out)
