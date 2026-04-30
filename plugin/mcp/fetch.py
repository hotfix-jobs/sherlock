"""Lazy fetch + cache for Sherlock's local data.

The SQLite index and per-framework markdown bundles are published as GitHub
Release assets by the build pipeline. The index is downloaded on first use;
framework bundles are fetched on demand the first time a page in that
framework is read.
"""
from __future__ import annotations

import os
import tarfile
import urllib.request
from pathlib import Path

import zstandard as zstd

RELEASE_BASE = os.environ.get(
    "SHERLOCK_RELEASE_BASE",
    "https://github.com/hotfix-jobs/sherlock/releases/latest/download",
)

DATA_DIR = Path(
    os.environ.get(
        "SHERLOCK_DATA_DIR", Path.home() / ".claude" / "data" / "sherlock"
    )
)
INDEX_DB = DATA_DIR / "index.db"
MD_DIR = DATA_DIR / "markdown"
MANIFEST = DATA_DIR / "manifest.json"


def index_db_path() -> Path:
    return INDEX_DB


def ensure_index() -> None:
    if INDEX_DB.exists():
        return
    update_index_db(force=True)


def update_index_db(force: bool = False) -> str:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if INDEX_DB.exists() and not force:
        return f"Index already present at {INDEX_DB}"

    _download_zst(f"{RELEASE_BASE}/index.db.zst", INDEX_DB)

    try:
        with urllib.request.urlopen(f"{RELEASE_BASE}/manifest.json") as r:
            MANIFEST.write_bytes(r.read())
    except Exception:
        pass

    return f"Index updated: {INDEX_DB} ({INDEX_DB.stat().st_size // 1024} KB)"


def install_framework_bundle(name: str) -> str:
    name = name.lower()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = MD_DIR / name
    if target.exists() and any(target.iterdir()):
        return f"{name} already installed at {target}"

    tmp = DATA_DIR / f"{name}.tar"
    _download_zst(f"{RELEASE_BASE}/sherlock-{name}.tar.zst", tmp)
    MD_DIR.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tmp) as tf:
        tf.extractall(MD_DIR)
    tmp.unlink()
    return f"Installed {name} to {target}"


def framework_is_installed(name: str) -> bool:
    p = MD_DIR / name.lower()
    return p.exists() and any(p.iterdir())


def read_doc(path: str) -> str:
    """Read markdown by path. On miss, auto-install the framework bundle."""
    path = path.strip().lstrip("/")
    if not path.endswith(".md"):
        path = path + ".md"

    local = MD_DIR / path
    if local.exists():
        return local.read_text(encoding="utf-8")

    framework = path.split("/", 1)[0]
    try:
        install_framework_bundle(framework)
    except Exception as e:
        return (
            f"Could not fetch {path}: {e}\n\n"
            f"Verify the path is correct (search_apple_docs returns valid paths) "
            f"and that framework '{framework}' exists in the index."
        )

    if local.exists():
        return local.read_text(encoding="utf-8")
    return f"Path {path} not found in framework '{framework}' bundle."


def _download_zst(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r:
        compressed = r.read()
    dctx = zstd.ZstdDecompressor()
    dest.write_bytes(dctx.decompress(compressed))
