# Sherlock

> Apple Developer documentation, instantly searchable in Claude Code.

Sherlock is a [Claude Code](https://claude.com/claude-code) plugin that gives Claude search and read access to the entire Apple Developer documentation corpus (Swift, SwiftUI, UIKit, Foundation, Combine, Core Data, SwiftData, Core ML, MapKit, AVFoundation, and more) without leaving your editor.

Named after [Apple's original macOS search app](https://en.wikipedia.org/wiki/Sherlock_(software)) (and the dev folklore around it), Sherlock indexes ~70,000 symbols into a SQLite FTS5 database and serves them to Claude as MCP tools.

## Works great with Superpowers

Sherlock pairs naturally with the [Superpowers](https://github.com/obra/superpowers) Claude Code plugin. Use Superpowers' brainstorming, planning, and TDD skills to figure out *what* to build; Sherlock grounds the *how* in Apple's actual API surface. The skills in this plugin defer to Superpowers when both are installed, so you get composition rather than overlap.

## Install

```
/plugin install sherlock
```

Pre-marketplace: clone this repo and add it as a local plugin in `~/.claude/settings.json`.

## What you get

Five MCP tools your agent can call directly:

| Tool | Use |
|---|---|
| `search_apple_docs` | Ranked FTS5 search across all indexed Apple docs |
| `read_apple_doc` | Full markdown for one page (auto-installs framework on first read) |
| `list_frameworks` | Show what's indexed and what's installed locally |
| `install_framework` | Bulk-download a framework for full offline mode |
| `update_index` | Pull the latest weekly index release |

Plus a [skill](plugin/skills/docs/SKILL.md) that teaches Claude when to reach for these tools.

## How it works

```
┌──────────────────────┐         ┌────────────────────┐
│  GitHub Actions (CI) │         │  Your machine      │
│                      │         │                    │
│  weekly cron:        │ Release │  /plugin install   │
│  - crawl Apple docs  │ ──────▶ │  sherlock          │
│  - build markdown    │   .zst  │                    │
│  - build FTS5 index  │         │  first tool call:  │
│  - publish artifacts │         │  - DL index (~50MB)│
└──────────────────────┘         │  - DL frameworks   │
                                 │    on demand       │
                                 └────────────────────┘
```

- **Index DB** (~50 MB) downloads once on first tool call → `~/.claude/data/sherlock/index.db`
- **Per-framework markdown bundles** (~10–30 MB each) fetched the first time you read a page in that framework
- All data is cached locally; subsequent reads are instant
- Corpus rebuilt weekly from developer.apple.com

Override paths with `SHERLOCK_DATA_DIR` and `SHERLOCK_RELEASE_BASE` env vars.

## Repo layout

```
sherlock/
├── plugin/                    # what users install
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── skills/docs/
│   │   └── SKILL.md
│   └── mcp/                   # MCP server (Python)
│       ├── server.py
│       ├── search.py          # SQLite FTS5
│       ├── fetch.py           # lazy install + cache
│       └── requirements.txt
│
├── scripts/                   # CI build pipeline (users never run these)
│   ├── build_corpus.py        # streaming async crawler + indexer
│   └── requirements.txt
│
└── .github/workflows/
    └── build-corpus.yml       # weekly Mon 06:00 UTC + manual dispatch
```

## Building the corpus

End users never build the corpus. The whole architecture exists so they don't have to: GitHub Actions runs the crawl once a week and publishes ready-to-use artifacts to [Releases](https://github.com/hotfix-jobs/sherlock/releases). The plugin downloads those.

### Triggering a fresh build (org admins)

```
gh workflow run build-corpus.yml
```

Or trigger a partial build for one framework via the workflow's manual-dispatch input.

### Local development of the plugin

You do not need to re-crawl Apple. Point `SHERLOCK_RELEASE_BASE` at the live Releases URL (or any HTTP server hosting a prior `index.db.zst` and `sherlock-*.tar.zst`) and run the MCP server.

### Local development of the build pipeline itself

One streaming script does discovery, fetch, markdown conversion, and SQLite FTS5 indexing in a single pass. Test it against one framework:

```bash
pip install -r scripts/requirements.txt
python scripts/build_corpus.py --frameworks swiftui --out-dir dist
```

That writes `dist/index.db`, `dist/markdown/swiftui/...`, and `dist/manifest.json`. Tune `--concurrency` (default 16) up or down based on what Apple's servers tolerate; the script backs off automatically on 429s.

### What the script does

1. Auto-discovers framework slugs from `developer.apple.com/documentation/` (or accepts an explicit `--frameworks` list)
2. BFS-crawls each framework's JSON API with HTTP/2 connection pooling and a configurable concurrency cap
3. Converts each page's JSON to markdown in memory
4. Writes the markdown file and inserts an FTS5 row in the same loop
5. Never persists raw JSON to disk

No three-step pipeline, no intermediate `raw-json/` directory, no manifest tracking between phases.

## Contributing

PRs welcome. Most useful contributions:

- Adding new framework slugs to the fallback list in `scripts/build_corpus.py`
- Improving the JSON-to-markdown converter for cleaner output
- New MCP tools (e.g., symbol-graph traversal, deprecation lookups)
- Reducing the index size (better summary extraction, smarter FTS tokenization)

## License

MIT (see [LICENSE](LICENSE)). Documentation content © Apple Inc., redistributed for offline AI/developer reference. Not affiliated with Apple.

## Credits

Built by [Hotfix](https://hotfix.jobs).
