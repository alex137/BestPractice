# Grok Build adapter

**New 2026-09-17, researched but not yet run.** Grok Build (`xai-org/grok-build`)
is xAI's own terminal coding agent — a real product with shell and file
access, not the plain chat-only Grok this repo's other guides used to treat
as unverified. Everything below is grounded in xAI's own current
documentation, found and read on 2026-09-17; nothing here has been
confirmed by an actual Grok Build session working in this repo yet — that
is exactly what [spec/PROVIDER_PORTABILITY_PLAN.md](../../spec/PROVIDER_PORTABILITY_PLAN.md)'s
Phase 5 test is for.

Grok reads **`AGENTS.md` natively** — no pointer file needed; xAI's own
docs say it also reads `CLAUDE.md` and `.claude/` (skills, agents, Model
Context Protocol (MCP) servers, hooks, rules) directly, which is broader
compatibility than Codex or Gemini CLI claim. **Whether that extends to
actually firing this repo's `.claude/hooks/*.sh` the way Claude Code's own
`SessionStart` protocol does is unverified** — "auto-reads" is not the same
claim as "auto-executes with the same event semantics," and nothing found
so far distinguishes the two.

Wiring the rest:

- **Bootstrap:** Grok Build has its own hook system — lifecycle hooks
  configured in `.grok/hooks.json`, receiving `$GROK_EVENT`, `$GROK_MESSAGE`
  and `$GROK_SESSION_ID` in the environment (per `grok inspect`, which
  lists what Grok discovered: config sources, instructions, skills,
  plugins, hooks, MCP servers). **The exact event name for "session start"
  and the JSON shape `.grok/hooks.json` expects are not written down
  here on purpose** — xAI's docs move fast enough that guessing at the
  syntax risks shipping something that silently fails to parse. Check
  `docs.x.ai/build`'s current hooks reference, then wire a session-start
  hook to `bash tools/bootstrap.sh`, the same harness-neutral script Codex
  and Gemini CLI both use.
- **Pre-approved commands:** unresearched — not found in what this pass
  covered.
- **Commit identity and signing:** `tools/bootstrap.sh` calls
  `.claude/hooks/commit-identity.sh` automatically, the moment a
  session-start hook is wired per the Bootstrap step above — same
  guarantee level as Codex and Gemini CLI (hard if the hook is actually
  configured, none at all if it isn't). See [../LEDGER.md](../LEDGER.md)
  for this mechanism's own history. One thing specific to Grok worth
  testing directly: `commit-identity.sh`'s GitHub-account-lookup fallback
  now sends a bearer token when `GH_TOKEN` or `GITHUB_TOKEN` is set in the
  environment (2026-09-17) — whether a Grok Build session's own
  environment carries either of those by default is exactly the kind of
  thing Phase 5's test would answer and this research pass could not.

**This adapter is not yet wired into `templates/harness/LEDGER.md`'s
enforced transfer tracking** — that check's member-directory list
(`tools/precedent_check.py`) is hardcoded to the original three and would
need its own change to add a fourth. Deliberately deferred rather than
done by guess: extending an enforced check on unverified assumptions about
a hooks syntax this pass could not confirm is a worse mistake than leaving
the gap named.
