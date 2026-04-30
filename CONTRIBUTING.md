# Contributing to Sherlock

Thanks for considering a contribution. Sherlock is small and opinionated, so please skim this before opening a large PR.

## What we love

- Bug reports with minimal reproductions
- Improvements to the JSON-to-markdown converter (`scripts/build_corpus.py`)
- New MCP tools that solve a specific developer workflow
- New skills, but only if they prevent a documented failure mode (see the `superpowers:writing-skills` philosophy)
- Better summary extraction or smarter FTS5 tokenization
- Documentation fixes

## What needs discussion first

Open an issue before starting work on:

- Adding new dependencies (we keep the surface small)
- Changes to the plugin or marketplace manifest schema
- Anything that changes how data is downloaded or cached
- Skills that overlap with what the existing three already do

## Local development

### Testing the MCP server

```bash
pip install -r plugin/mcp/requirements.txt
SHERLOCK_DATA_DIR=/tmp/sherlock python3 plugin/mcp/server.py
```

The server speaks MCP over stdio. Connect any MCP client to test the tools.

### Testing the build pipeline

Build one framework end-to-end (takes a few seconds):

```bash
pip install -r scripts/requirements.txt
python scripts/build_corpus.py --frameworks swiftdata --out-dir /tmp/test-build
```

Verify the output:

- `/tmp/test-build/index.db` (SQLite FTS5)
- `/tmp/test-build/markdown/swiftdata/...md`
- `/tmp/test-build/manifest.json`

### Validating the plugin manifest

```bash
claude plugin validate .
```

CI runs this on every PR, so manifest errors are caught before merge.

## PR expectations

1. One logical change per PR
2. No em dashes in any committed text (use periods, semicolons, colons, or parens). CI enforces this.
3. Update the relevant SKILL.md or README if behavior changes
4. If you're touching the build pipeline, smoke-test against at least one small framework
5. Squash commits before merging (we keep history linear)

## License

By submitting a contribution, you agree that your code is licensed under the MIT license that covers Sherlock (see [LICENSE](LICENSE)). You retain copyright on your contribution.

## Code of conduct

Be civil. We follow the principle of "would the maintainers be annoyed reading this?" If yes, rewrite it.
