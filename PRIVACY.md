# Privacy Policy

**Last updated:** April 30, 2026

Sherlock is a local Claude Code plugin and MCP server that reads Apple Developer documentation. This document describes exactly what data Sherlock processes, transmits, and stores.

## What Sherlock does NOT do

Sherlock does not:

- Collect, transmit, or store any personally identifiable information
- Send telemetry, analytics, or usage metrics to any server
- Track which queries you make, which docs you read, or how often you use the plugin
- Phone home to Hotfix, Anthropic, or any third party
- Share data with advertisers or marketing platforms
- Require an account, login, or API key

## What Sherlock does do

When you install or use Sherlock, the following happens entirely on your local machine, with one exception (item 1):

1. **Downloads from GitHub Releases.** On first use, Sherlock downloads a SQLite index file (~50-100 MB) from the public GitHub Releases of `https://github.com/hotfix-jobs/sherlock`. When you read documentation for a framework you have not used before, Sherlock downloads that framework's markdown bundle from the same Releases URL. These are unauthenticated public HTTPS requests; GitHub may log them per their own privacy policy (https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement), but Hotfix has no access to those logs.

2. **Caches docs locally.** Downloaded docs are stored at `~/.claude/data/sherlock/` on your machine. Nothing is uploaded.

3. **Searches the local index.** Search queries you ask Claude about are processed by the local SQLite database. They never leave your machine.

4. **Returns markdown to Claude.** When Claude calls a Sherlock MCP tool, the result is returned to your local Claude Code session. Whether Claude itself transmits that text to Anthropic's API is governed by Anthropic's privacy policy, not Sherlock's.

## Data location

All Sherlock data lives at `~/.claude/data/sherlock/` on your local filesystem. You can delete this directory at any time to remove all cached docs. Override the location with the `SHERLOCK_DATA_DIR` environment variable.

## Source code

Sherlock is open source under the MIT license. You can audit exactly what the plugin does at https://github.com/hotfix-jobs/sherlock.

## Contact

Questions about this policy: support@hotfix.jobs

## Changes

Material changes to this policy will be reflected in this file's git history at https://github.com/hotfix-jobs/sherlock/commits/main/PRIVACY.md.
