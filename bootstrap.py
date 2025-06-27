#!/usr/bin/env python3
import subprocess
import os
import sys
import requests
from urllib.parse import urlparse

REPO_PATH = os.path.dirname(os.path.abspath(__file__))
OFFLINE_DIR = os.path.join(REPO_PATH, "offline_pages")

URLS_TO_FETCH = [
    # dodaj kolejne adresy (HTML lub bezpośrednie linki do JPG/PNG)
]


def git_pull():
    print("🔄 Running git pull...")
    result = subprocess.run(
        ["git", "-C", REPO_PATH, "pull"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✔ git pull succeeded")
    else:
        print("✖ git pull failed:")
        print(result.stdout, result.stderr)
        sys.exit(1)


def fetch_pages():
    os.makedirs(OFFLINE_DIR, exist_ok=True)
    for url in URLS_TO_FETCH:
        print(f"📥 Fetching {url} ...")
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            ctype = resp.headers.get("Content-Type", "")
            parsed = urlparse(url)
            # nazwa pliku na podstawie ścieżki URL
            base = parsed.path.strip("/").replace("/", "_") or "index"
            if "image" in ctype:
                # np. image/jpeg → jpg
                ext = ctype.split("/")[-1]
                fname = os.path.join(OFFLINE_DIR, f"{base}.{ext}")
                with open(fname, "wb") as f:
                    f.write(resp.content)
                print(f"  → saved image to {fname}")
            else:
                # traktujemy jako HTML
                fname = os.path.join(OFFLINE_DIR, f"{base}.html")
                with open(fname, "w", encoding=resp.encoding or "utf-8") as f:
                    f.write(resp.text)
                print(f"  → saved HTML to {fname}")
        except Exception as e:
            print(f"  ✖ error fetching {url}: {e}")


if __name__ == "__main__":
    git_pull()
    fetch_pages()
    print("🎉 Bootstrap complete.")
