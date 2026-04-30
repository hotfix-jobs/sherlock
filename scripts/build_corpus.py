#!/usr/bin/env python3
"""Sherlock corpus builder.

Streams Apple Developer documentation from developer.apple.com into a
SQLite FTS5 index and per-framework markdown bundles in a single pass.

This is the entire build pipeline; nothing intermediate is persisted.
JSON arrives, becomes markdown in memory, and is written to disk as
both a markdown file and an FTS5 row.

Usage:
  python scripts/build_corpus.py
  python scripts/build_corpus.py --frameworks swiftui uikit
  python scripts/build_corpus.py --concurrency 32 --out-dir dist
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import yaml

API_BASE = "https://developer.apple.com/tutorials/data/documentation"
ROOT_INDEX_URL = "https://developer.apple.com/tutorials/data/documentation/technologies.json"
NON_FRAMEWORK_SLUGS = {
    "technologies", "technologyoverviews", "samplecode", "updates",
    "tutorials",
}
USER_AGENT = "Sherlock/0.1 (+https://github.com/hotfix-jobs/sherlock)"
HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
DEFAULT_CONCURRENCY = 16

FALLBACK_FRAMEWORKS = [
    "swift", "swiftui", "uikit", "appkit", "foundation", "combine",
    "coredata", "swiftdata", "coreml", "mapkit", "avfoundation",
    "cloudkit", "watchkit", "widgetkit", "userinterface",
]


def normalize_path(identifier: str) -> str | None:
    """Convert any Apple identifier or URL to a canonical lowercase path.

    Apple's documentation URLs are case-insensitive, and the same symbol
    is referenced with different casings throughout the JSON (e.g.
    `SwiftData/ModelContext/insert(_:)` and `swiftdata/modelcontext/insert(_:)`).
    Lowercasing the whole path ensures one canonical identifier per page
    and avoids both index duplicates and case-collision issues on
    case-insensitive filesystems.
    """
    if not identifier:
        return None
    s = identifier
    if s.startswith("doc://"):
        s = s[len("doc://"):]
        if s.startswith("com.apple."):
            s = s[len("com.apple."):]
        if "/documentation/" in s:
            _, _, s = s.partition("/documentation/")
    for prefix in ("/documentation/", "documentation/"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    s = s.strip("/").lower()
    return s or None


def extract_refs(data: dict, framework: str) -> set[str]:
    """Pull every in-framework documentation reference out of one page."""
    refs: set[str] = set()
    fprefix = f"{framework}/"

    def add(ident: str | None) -> None:
        n = normalize_path(ident or "")
        if n and (n == framework or n.startswith(fprefix)):
            refs.add(n)

    for section in data.get("topicSections") or []:
        for ident in section.get("identifiers") or []:
            add(ident)
    for section in data.get("relationshipsSections") or []:
        for ident in section.get("identifiers") or []:
            add(ident)
    for section in data.get("seeAlsoSections") or []:
        for ident in section.get("identifiers") or []:
            add(ident)

    valid_kinds = {
        "topic", "method", "property", "class", "structure", "protocol",
        "enum", "function", "macro", "typealias", "module", "framework",
        "init", "case", "subscript", "associatedtype", "operator",
    }
    for ref_id, ref_data in (data.get("references") or {}).items():
        if not isinstance(ref_data, dict):
            continue
        if ref_data.get("type") in valid_kinds:
            add(ref_data.get("url") or ref_data.get("identifier") or ref_id)

    return refs


async def discover_frameworks(client: httpx.AsyncClient) -> list[str]:
    """Auto-discover framework slugs from Apple's documentation root."""
    try:
        r = await client.get(ROOT_INDEX_URL)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Discovery failed ({e}); falling back to known framework list.", file=sys.stderr)
        return list(FALLBACK_FRAMEWORKS)

    slugs: set[str] = set()
    for ref_data in (data.get("references") or {}).values():
        if not isinstance(ref_data, dict):
            continue
        url = ref_data.get("url", "")
        if not url.startswith("/documentation/"):
            continue
        rest = url[len("/documentation/"):].strip("/")
        if rest and "/" not in rest:
            slug = rest.lower()
            if slug not in NON_FRAMEWORK_SLUGS:
                slugs.add(slug)

    if not slugs:
        return list(FALLBACK_FRAMEWORKS)
    return sorted(slugs)


def render_inline(items: list | None, refs: dict) -> str:
    if not items:
        return ""
    out: list[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        t = it.get("type")
        if t == "text":
            out.append(it.get("text", ""))
        elif t == "codeVoice":
            out.append(f"`{it.get('code', '')}`")
        elif t == "emphasis":
            out.append(f"*{render_inline(it.get('inlineContent'), refs)}*")
        elif t == "strong":
            out.append(f"**{render_inline(it.get('inlineContent'), refs)}**")
        elif t == "reference":
            ident = it.get("identifier", "")
            ref = refs.get(ident, {})
            text = render_inline(ref.get("titleInlineContent"), refs) or ref.get("title") or ident
            url = ref.get("url", "")
            out.append(f"[{text}]({url})" if url else text)
        elif t == "link":
            out.append(f"[{it.get('title') or it.get('destination', '')}]({it.get('destination', '')})")
        elif t == "newTerm":
            out.append(render_inline(it.get("inlineContent"), refs))
        elif t == "image":
            ref = refs.get(it.get("identifier", ""), {})
            url = next((v.get("url", "") for v in (ref.get("variants") or []) if v.get("url")), "")
            alt = ref.get("alt", "image")
            out.append(f"![{alt}]({url})" if url else f"[{alt}]")
        else:
            sub = it.get("inlineContent") or it.get("content")
            if isinstance(sub, list):
                out.append(render_inline(sub, refs))
    return "".join(out)


def render_block(block: dict, refs: dict) -> str:
    t = block.get("type")
    if t == "paragraph":
        return render_inline(block.get("inlineContent"), refs) + "\n"
    if t == "heading":
        return f"\n{'#' * block.get('level', 2)} {block.get('text', '')}\n"
    if t == "codeListing":
        syntax = block.get("syntax") or ""
        code = "\n".join(block.get("code") or [])
        return f"\n```{syntax}\n{code}\n```\n"
    if t in ("unorderedList", "orderedList"):
        items = block.get("items") or []
        ordered = t == "orderedList"
        lines: list[str] = []
        for i, item in enumerate(items, 1):
            inner = "\n".join(
                render_block(b, refs).rstrip() for b in (item.get("content") or [])
            )
            prefix = f"{i}. " if ordered else "- "
            lines.append(f"{prefix}{inner}")
        return "\n".join(lines) + "\n"
    if t == "aside":
        kind = (block.get("style") or "note").capitalize()
        inner = "\n".join(render_block(b, refs).rstrip() for b in (block.get("content") or []))
        return f"\n> **{kind}:** {inner}\n"
    if t == "termList":
        out = []
        for item in block.get("items") or []:
            term = render_inline(item.get("term", {}).get("inlineContent"), refs)
            defn = "\n".join(render_block(b, refs).rstrip() for b in (item.get("definition", {}).get("content") or []))
            out.append(f"- **{term}**: {defn}")
        return "\n".join(out) + "\n"
    return ""


def json_to_markdown(data: dict, framework: str, path: str) -> tuple[str, str, str, str]:
    """Convert an Apple JSON page into (markdown, summary, kind, title)."""
    meta = data.get("metadata", {}) or {}
    refs = data.get("references", {}) or {}

    title = meta.get("title", path.split("/")[-1])
    role = (meta.get("role") or "").lower()

    fm: dict = {"title": title}
    if role:
        fm["kind"] = role
    if meta.get("symbolKind"):
        fm["symbol_kind"] = meta["symbolKind"]
    if meta.get("modules"):
        fm["framework"] = (meta["modules"][0].get("name") or framework).lower()

    platforms = []
    for p in meta.get("platforms") or []:
        if not p.get("name"):
            continue
        entry = {"name": p["name"]}
        if p.get("introducedAt"):
            entry["since"] = p["introducedAt"]
        if p.get("deprecatedAt"):
            entry["deprecated"] = p["deprecatedAt"]
        if p.get("beta"):
            entry["beta"] = True
        platforms.append(entry)
    if platforms:
        fm["platforms"] = platforms
    if meta.get("deprecatedAt"):
        fm["deprecated_at"] = meta["deprecatedAt"]

    out: list[str] = ["---", yaml.safe_dump(fm, sort_keys=False).strip(), "---", "", f"# {title}", ""]

    summary = render_inline(data.get("abstract"), refs).strip()
    if summary:
        out.extend([summary, ""])

    for section in data.get("primaryContentSections") or []:
        kind = section.get("kind")
        if kind == "declarations":
            for decl in section.get("declarations") or []:
                tokens = decl.get("tokens") or []
                code = "".join(t.get("text", "") for t in tokens)
                lang = (decl.get("languages") or ["swift"])[0]
                out.extend(["", f"```{lang}", code, "```", ""])
        elif kind == "content":
            for block in section.get("content") or []:
                out.append(render_block(block, refs))
        elif kind == "parameters":
            params = section.get("parameters") or []
            if params:
                out.extend(["", "## Parameters", ""])
                for p in params:
                    body = "\n".join(render_block(b, refs).rstrip() for b in (p.get("content") or []))
                    out.append(f"- `{p.get('name', '')}`: {body}")
                out.append("")
        elif kind == "returnValue":
            out.extend(["", "## Return value", ""])
            for block in section.get("content") or []:
                out.append(render_block(block, refs))

    topic_sections = data.get("topicSections") or []
    if topic_sections:
        out.extend(["", "## Topics", ""])
        for ts in topic_sections:
            tname = ts.get("title", "")
            if tname:
                out.append(f"\n### {tname}\n")
            for ident in ts.get("identifiers") or []:
                ref = refs.get(ident, {})
                rtitle = ref.get("title") or ident
                rurl = ref.get("url", "")
                out.append(f"- [{rtitle}]({rurl})" if rurl else f"- {rtitle}")
            out.append("")

    md = re.sub(r"\n{3,}", "\n\n", "\n".join(out))
    return md, (summary[:240] if summary else ""), role, title


@dataclass
class CrawlState:
    discovered: set[str] = field(default_factory=set)
    completed: set[str] = field(default_factory=set)
    failed: set[str] = field(default_factory=set)
    rate_limit_hits: int = 0


async def fetch_page(
    client: httpx.AsyncClient,
    path: str,
    sem: asyncio.Semaphore,
    state: CrawlState,
) -> dict | None:
    # Apple's CDN/WAF blocks any URL containing "..." as a path-traversal
    # false positive. Affects Swift range operators (...) and (..<) and their
    # synthesized variants on Int/Double/String/etc. Skip silently.
    if "..." in path or "..<" in path:
        return None

    url = f"{API_BASE}/{path}.json"
    backoff = 1.0
    for _ in range(5):
        async with sem:
            try:
                r = await client.get(url)
            except httpx.HTTPError as e:
                state.failed.add(path)
                print(f"  ! {path}: {e}", file=sys.stderr)
                return None
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:
                state.failed.add(path)
                print(f"  ! {path}: bad JSON ({e})", file=sys.stderr)
                return None
        if r.status_code == 404:
            return None
        if r.status_code == 429:
            state.rate_limit_hits += 1
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)
            continue
        state.failed.add(path)
        print(f"  ! {path}: HTTP {r.status_code}", file=sys.stderr)
        return None
    state.failed.add(path)
    return None


def init_db(out_db: Path) -> sqlite3.Connection:
    out_db.parent.mkdir(parents=True, exist_ok=True)
    if out_db.exists():
        out_db.unlink()
    con = sqlite3.connect(out_db)
    con.executescript(
        """
        CREATE TABLE docs (
            rowid     INTEGER PRIMARY KEY,
            path      TEXT UNIQUE,
            framework TEXT,
            title     TEXT,
            kind      TEXT,
            summary   TEXT
        );
        CREATE INDEX idx_docs_framework ON docs(framework);
        CREATE INDEX idx_docs_kind ON docs(kind);
        CREATE VIRTUAL TABLE docs_fts USING fts5(
            title, summary, body,
            content=''
        );
        """
    )
    return con


async def build_framework(
    framework: str,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    out_dir: Path,
    db: sqlite3.Connection,
    rowid_counter: list[int],
) -> int:
    state = CrawlState()
    state.discovered.add(framework)
    indexed = 0

    while True:
        pending = state.discovered - state.completed - state.failed
        if not pending:
            break

        batch = sorted(pending)
        print(f"  {framework}: fetching {len(batch)} (total {len(state.discovered)})")

        results = await asyncio.gather(*[fetch_page(client, p, sem, state) for p in batch])

        for path, data in zip(batch, results):
            state.completed.add(path)
            if not data:
                continue

            try:
                md, summary, kind, title = json_to_markdown(data, framework, path)
            except Exception as e:
                print(f"  ! {path}: convert failed ({e})", file=sys.stderr)
                continue

            md_path = out_dir / "markdown" / f"{path}.md"
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md, encoding="utf-8")

            rowid_counter[0] += 1
            rid = rowid_counter[0]
            db.execute(
                "INSERT INTO docs (rowid, path, framework, title, kind, summary) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (rid, path, framework, title, kind, summary),
            )
            db.execute(
                "INSERT INTO docs_fts (rowid, title, summary, body) VALUES (?, ?, ?, ?)",
                (rid, title, summary, md),
            )
            indexed += 1

            for ref in extract_refs(data, framework):
                if ref not in state.completed and ref not in state.failed:
                    state.discovered.add(ref)

        db.commit()

    note = f" ({state.rate_limit_hits} 429s)" if state.rate_limit_hits else ""
    print(f"  {framework}: {indexed} indexed, {len(state.failed)} failed{note}")
    return indexed


async def amain(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sem = asyncio.Semaphore(args.concurrency)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    limits = httpx.Limits(
        max_connections=args.concurrency * 2,
        max_keepalive_connections=args.concurrency,
    )

    async with httpx.AsyncClient(
        http2=True,
        timeout=HTTP_TIMEOUT,
        headers=headers,
        limits=limits,
        follow_redirects=True,
    ) as client:
        if args.frameworks:
            frameworks = [f.lower() for f in args.frameworks]
            print(f"Frameworks: {frameworks}")
        else:
            print("Discovering frameworks...")
            frameworks = await discover_frameworks(client)
            print(f"Discovered {len(frameworks)} frameworks")

        db = init_db(out_dir / "index.db")
        rowid_counter = [0]
        start = time.time()

        for fw in frameworks:
            print(f"\n=== {fw} ===")
            await build_framework(fw, client, sem, out_dir, db, rowid_counter)

        print("\nFinalizing index...")
        db.execute("INSERT INTO docs_fts(docs_fts) VALUES('optimize')")
        db.commit()
        db.close()

        manifest = {
            "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "frameworks": frameworks,
            "total_pages": rowid_counter[0],
            "duration_seconds": int(time.time() - start),
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

        print(f"\nDone. {rowid_counter[0]} pages in {int(time.time() - start)}s.")
        print(f"  index:    {out_dir / 'index.db'}")
        print(f"  markdown: {out_dir / 'markdown'}")
        print(f"  manifest: {out_dir / 'manifest.json'}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the Sherlock corpus.")
    ap.add_argument("--frameworks", nargs="+",
                    help="Frameworks to crawl (default: auto-discover)")
    ap.add_argument("--out-dir", default="dist", help="Output directory (default: dist)")
    ap.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                    help=f"Max concurrent HTTP requests (default: {DEFAULT_CONCURRENCY})")
    args = ap.parse_args()
    asyncio.run(amain(args))


if __name__ == "__main__":
    main()
