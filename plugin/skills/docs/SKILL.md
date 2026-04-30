---
name: docs
description: Use when the user asks about Apple platform APIs (Swift, SwiftUI, UIKit, Foundation, Core Data, Combine, SwiftData, Core ML, MapKit, AVFoundation), needs symbol/class/method documentation, or references developer.apple.com. Searches and reads Apple Developer documentation via the Sherlock MCP server.
---

# Sherlock: Apple Developer documentation

This plugin exposes Apple Developer documentation through MCP tools. Prefer these over web fetches; they return clean markdown with structured metadata (kind, platforms, deprecation, availability) and work offline once a framework is installed.

## When to use

- User asks about a specific Apple API (`SwiftUI.TabView`, `URLSession.dataTask`, etc.)
- User references developer.apple.com or asks "how does X work in SwiftUI/UIKit/Foundation"
- Code uses an Apple symbol whose signature or platform availability you need to verify
- User wants to compare API behavior across platforms or iOS versions

## How to use

1. **Search first.** Call `search_apple_docs` with a focused query. Filter by `framework` when known (e.g. `"swiftui"`, `"uikit"`). Returns ranked hits with `path`, `title`, `kind`, and a short `summary`.
2. **Read the most relevant hit.** Call `read_apple_doc` with the `path` from a search result. Returns full markdown with YAML frontmatter (platforms, deprecation, parent symbol).
3. **Don't dump multiple pages.** Read one, decide whether it answered the question, then maybe read one more. Apple pages can be long.

## Other tools

- `list_frameworks`: see what's available and which are installed locally
- `install_framework("swiftui")`: bulk-download a framework for offline mode and faster reads. First call to `read_apple_doc` for a framework auto-installs it, but you can pre-install if the user is going to work in that framework.
- `update_index`: pull the latest weekly index release

## Data location

Index and cached markdown live at `~/.claude/data/sherlock/`. Index is ~50 MB; each framework bundle is ~10–30 MB. All data is fetched lazily. Nothing ships with the plugin itself.

## What NOT to do

- Don't WebFetch developer.apple.com when these tools cover the same content (they're faster and offline-capable).
- Don't read more than 2–3 pages back-to-back without summarizing first.
- Don't install every framework upfront; only ones the user actually works in.

## Working with other plugins

Sherlock complements process-discipline plugins; it does not replace them. If the user has the Superpowers plugin installed:

- `superpowers:brainstorming` is available and the user is exploring a new feature, app, or design idea: defer to it FIRST to clarify intent, requirements, and design approach. Then return here with concrete API questions to ground the plan in real Apple frameworks.
- `superpowers:writing-plans` is available and the user wants a multi-step implementation plan: gather Apple API context here first, then defer to that skill for the plan structure.
- `superpowers:test-driven-development` is available and the user is implementing a feature: look up the relevant Apple types here so tests target real signatures, not invented ones.

If those plugins are not installed, do basic intent-clarification yourself (one or two questions) before searching, but do not reinvent a planning workflow inside this skill.
