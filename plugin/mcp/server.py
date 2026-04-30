"""Sherlock MCP server.

Exposes search + read tools over the Apple Developer documentation index,
backed by a SQLite FTS5 database and a lazy markdown cache populated from
GitHub Release artifacts.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

from search import list_frameworks_status, search_index
from fetch import (
    ensure_index,
    install_framework_bundle,
    read_doc,
    update_index_db,
)

mcp = FastMCP("apple")


@mcp.tool()
def search_apple_docs(
    query: str,
    framework: str | None = None,
    kind: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Full-text search across Apple Developer documentation.

    Args:
        query: Search terms. FTS5 syntax supported (quotes for phrases, OR/NOT operators).
        framework: Optional framework slug filter (e.g. "swiftui", "uikit").
        kind: Optional symbol kind filter (e.g. "class", "method", "property", "protocol").
        limit: Max results (default 10).

    Returns: list of {path, title, framework, kind, summary, score}.
    """
    ensure_index()
    return search_index(query, framework=framework, kind=kind, limit=limit)


@mcp.tool()
def read_apple_doc(path: str) -> str:
    """Read full markdown for an Apple doc page.

    Auto-installs the framework bundle on first read if not cached.

    Args:
        path: Doc path from a search result (e.g. "swiftui/tabview").

    Returns: markdown with YAML frontmatter.
    """
    return read_doc(path)


@mcp.tool()
def list_frameworks() -> list[dict]:
    """List frameworks available in the index, with installed/cached status."""
    ensure_index()
    return list_frameworks_status()


@mcp.tool()
def install_framework(name: str) -> str:
    """Bulk-download all markdown for a framework to enable offline mode.

    Args:
        name: Framework slug (e.g. "swiftui").
    """
    return install_framework_bundle(name)


@mcp.tool()
def update_index() -> str:
    """Force-download the latest weekly documentation index."""
    return update_index_db(force=True)


if __name__ == "__main__":
    mcp.run()
