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

**Wired into [../LEDGER.md](../LEDGER.md)'s enforced transfer tracking on
2026-09-21.** This section used to say the opposite, and the deferral was
half right: extending an enforced check on unverified assumptions about a
hooks syntax nobody has confirmed would indeed have been a guess. But the
ledger records *verdicts*, not wirings, and "nobody has confirmed whether
this can transfer" is a verdict — a more useful one than an absent column.
So the fourth member-directory went into
[`tools/precedent_check.py`](../../../tools/precedent_check.py)'s list,
every row dated before this adapter existed carries a backfilled cell
saying so, and the unverified-hooks caveat stayed exactly where it belongs:
in the Bootstrap bullet above, which still refuses to write down a syntax
it has not seen work.

This adapter's row in [../PARALLELS.md](../PARALLELS.md) is the other half:
what Claude Code does that this harness does not, mechanism by mechanism.

## The Markdown Check Does Not Run Here

**Read this before assuming your documents are checked.** On 2026-09-21
Precedent's Markdown lint left GitHub Actions entirely and was replaced by
`.claude/hooks/doc-lint-gate.sh`, which refuses a `git commit` whose staged
Markdown fails [doc_lint.py](../../../tools/doc_lint.py). That is a Claude Code mechanism: it needs a
`PreToolUse` hook, and Grok Build's own lifecycle hooks (`.grok/hooks.json`) may well be able
to carry it — but the event names and JSON shape are deliberately not written
down in this adapter, for the reason its Bootstrap section gives, so nothing
here claims a wiring that has not been run. **If you verify the hooks reference
and wire a pre-tool event to this script, say so in [../LEDGER.md](../LEDGER.md)**: it would be the
first hook row in that ledger with a real transfer to a third adapter.

**So on this adapter, nothing checks your Markdown before it reaches a
shared branch** — not the hook, and not CI, because the workflow the hook
replaced is retired and deleted. This is the first adapter gap with that
property. Every earlier one cost you a guard you never had; this one costs
you a guard that was there last week.

Do both of these. Not one:

1. **Run it yourself before every commit:**
   `python3 tools/doc_lint.py <the markdown you touched>`. Nothing will
   remind you.
2. **Put a GitHub check back**, because step 1 is a habit and a habit is
   what the hook exists to replace. Copy
   [../../github-actions/light-check.yml.template](../../github-actions/light-check.yml.template)
   to `.github/workflows/light-check.yml`, set its `CUSTOMIZE` command to
   `python3 tools/doc_lint.py` and its `paths:` to `"**/*.md"`, then enable
   Actions for the repository at **Settings → Actions**.

**Doing only the first is the arrangement that just failed upstream.** "A
session is supposed to run the check before committing" was written down
and followed for months, and still nothing refused a commit that skipped
it — which was only ever safe because CI was behind it.
