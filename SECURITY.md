# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in Sherlock, please report it privately so it can be fixed before public disclosure.

**Email:** support@hotfix.jobs

Include:

1. A description of the vulnerability
2. Steps to reproduce
3. The affected version (commit SHA or release tag)
4. Any relevant logs, screenshots, or proof-of-concept

We aim to acknowledge reports within 72 hours and to ship a fix or mitigation within 14 days for high-severity issues.

## Disclosure timeline

We follow coordinated disclosure:

1. You report the issue privately
2. We confirm and begin work on a fix
3. We agree on a public disclosure date with you
4. We ship the fix and publish an advisory on GitHub

If you have not heard back within 5 business days, escalate by opening a GitHub issue (without describing the vulnerability) tagging @hotfix-bot.

## Scope

In scope:

- The MCP server code in `plugin/mcp/`
- The corpus build pipeline in `scripts/build_corpus.py`
- The plugin manifest, marketplace manifest, and skill files
- The GitHub Actions workflow

Out of scope:

- Vulnerabilities in the Apple documentation content itself (report to Apple)
- Vulnerabilities in dependencies that are tracked by upstream advisories (Dependabot will surface these automatically)
- Issues that require physical access to a user's machine
- Social engineering of Hotfix staff

## Hall of fame

Contributors who report valid security issues will be credited in the release notes for the fix (with their permission).
