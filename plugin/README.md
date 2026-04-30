# Sherlock

> Apple Developer documentation, instantly searchable in Claude Code.

Sherlock is a Claude Code plugin (and MCP server) that gives Claude search and read access to the entire Apple Developer documentation corpus (Swift, SwiftUI, UIKit, Foundation, Combine, Core Data, SwiftData, Core ML, MapKit, AVFoundation, and more) without leaving your editor.

Named after Apple's original macOS search app (and the dev folklore around it), Sherlock indexes ~70,000 symbols into a SQLite FTS5 database and serves them as MCP tools.

## Install

```
/plugin install sherlock
```

(Pre-marketplace: clone this repo and point `~/.claude/settings.json` at `plugin/`.)

## Tools exposed

| Tool | Purpose |
|---|---|
| `search_apple_docs(query, framework?, kind?, limit?)` | Ranked FTS5 search across all indexed Apple docs |
| `read_apple_doc(path)` | Full markdown for one page (auto-installs framework on miss) |
| `list_frameworks()` | Show what's indexed and what's installed locally |
| `install_framework(name)` | Bulk-download a framework for full offline mode |
| `update_index()` | Pull the latest weekly index release |

## How it works

- **Index DB** (~50 MB) downloads once on first tool call → `~/.claude/data/sherlock/index.db`
- **Per-framework markdown bundles** (~10–30 MB each) fetched on demand the first time you read a page in that framework
- All data is cached locally; subsequent reads are instant
- Corpus rebuilt weekly from developer.apple.com via the build pipeline in this repo

Override paths with `SHERLOCK_DATA_DIR` and `SHERLOCK_RELEASE_BASE` env vars.

## Local development

```bash
pip install -r plugin/mcp/requirements.txt
SHERLOCK_DATA_DIR=/tmp/sherlock python3 plugin/mcp/server.py
```

Then connect an MCP client to test the tools.

## Building the corpus yourself

The `.github/workflows/build-corpus.yml` workflow runs weekly and publishes release artifacts (`index.db.zst`, per-framework `sherlock-*.tar.zst`, `manifest.json`). To run it manually:

```
gh workflow run build-corpus.yml
```

To run the streaming pipeline locally for one framework:

```bash
pip install -r scripts/requirements.txt
python scripts/build_corpus.py --frameworks swiftui --out-dir dist
```

## License

MIT. Documentation content © Apple Inc., redistributed for offline AI use.
