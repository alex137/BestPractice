# Claude-only surface — the parallel-coverage table

**What this file is for.** Claude Code is the harness this repository is
developed in, so every new mechanism gets built as a `.claude/` hook first
and the other three adapters find out later, or never. This table is the
standing answer to one question, asked once per mechanism rather than once
per change: **does codex, gemini-cli and grok-build have a parallel for
this, and if not, what does the person on that harness get instead?**

**It is not [LEDGER.md](LEDGER.md), and the difference is the whole
reason it exists.** The ledger is keyed by *change* — a commit touches a
member directory, a row records the per-member verdict for that commit. A
mechanism nobody has changed since it was written therefore has no ledger
row saying whether a parallel exists, and a mechanism that lives only in
`.claude/` and never in `templates/harness/claude-code/` has no ledger row
at all. This table is keyed by *mechanism*, so a gap stays visible whether
or not anyone touched it lately.

**Checked mechanically** by [`tools/precedent_check.py`](../../tools/precedent_check.py)'s
`claude-only-surface-has-a-parallel`: every hook in `.claude/hooks/` and
every hook `.claude/settings*.json` wires must appear in the table below
with a non-empty verdict in all three other columns, and a row naming a
mechanism that no longer exists is a finding too. **What it cannot check
is whether a verdict is still TRUE** — that is
[very-deep-check](../../practices/very-deep-check.md)'s pass 1, which
re-reads each `none —` cell against what the harness can do *today* rather
than what it could when the row was written.

**A `none` is a real answer.** Three of the rows below are `none` on every
non-Claude harness for the same structural reason: the harness has no
invocation point at that moment. Naming that is the point; papering over it
with a "the agent is supposed to remember" sentence is how the Markdown
gate came to be missing on three adapters at once.

| Mechanism | What it does | codex | gemini-cli | grok-build |
|---|---|---|---|---|
| `session-start.sh` | The `SessionStart` hook: deepens a shallow clone, renders `.precedent/SESSION_PRACTICES.md`, clones and refreshes declared sources, then runs the access, upstream-freshness, engine-freshness and beta-watermark notices | **[`tools/bootstrap.sh`](../../tools/bootstrap.sh)**, wired as the environment setup script. Parallel since 2026-09-21 and **not before**: the script ran three steps against the hook's seven, so the source clone, the source refresh and `SESSION_PRACTICES.md` — the file AGENTS.md's Standing instruction tells every session to read — reached no non-Claude session at all | same script, wired via the instructions-file directive in [`gemini-cli/GEMINI.md`](gemini-cli/GEMINI.md) — a *soft* guarantee (the agent has to actually run it) where Claude Code's is hard | same script, wired from `.grok/hooks.json`. **Unverified**: the event name and JSON shape are deliberately not written down ([`grok-build/README.md`](grok-build/README.md)), so this is a parallel that exists and has never been seen to fire |
| `commit-identity.sh` | Resolves the commit author, email and timezone to the person running the session rather than the container's agent account, and installs a `pre-commit` backstop that refuses an inferred identity | **[`tools/bootstrap.sh`](../../tools/bootstrap.sh)** calls it directly. The script needs nothing Claude-specific — it reads `$CLAUDE_PROJECT_DIR` and falls back to `$PWD` | same | same |
| `freshness-guard.sh` (`session-start` mode) | Fetch, fast-forward, and reconcile a diverged-but-clean checkout before the session's first read | **partial** — [`tools/bootstrap.sh`](../../tools/bootstrap.sh) carries its own inline fetch-and-fast-forward block covering the same moment. It does **not** carry the guard's divergence reconcile (rescue-ref then reset) or its `stale_checkout_hours` escalation, and the duplication is itself a standing finding: two implementations of one rule, and only one of them gets the fixes | same | same |
| `freshness-guard.sh` (`pre-write`, `user-prompt` modes) | Re-checks freshness before the first write, and again on an idle return | **none** — codex has no per-tool-call or prompt-submit invocation point. A session left open across a break is never rechecked | **none**, same reason | **none as written.** `.grok/hooks.json` has lifecycle hooks and may well have a pre-tool event; nobody has confirmed the event names, so nothing here claims a wiring that has not been run |
| `precedent-paths.sh` | `PreToolUse` on `Edit\|Write\|NotebookEdit`: prints the on-demand practices whose `applies_to` matches the file about to be written, once per session per rule | **none** — no pre-tool invocation point. The fallback is the Standing instruction's `python3 tools/precedent_paths.py FILE`, run by hand | **none**, same reason | **none as written**, same reason as the guard's pre-write mode |
| `doc-lint-gate.sh` | `PreToolUse` on `Bash`: refuses a `git commit` whose staged Markdown fails [`doc_lint.py`](../../tools/doc_lint.py) | **none.** The Markdown lint left GitHub Actions on 2026-09-21 and this hook replaced it, so on codex **nothing checks Markdown before it reaches a shared branch**. [`codex/README.md`](codex/README.md)'s own section says what to do instead: run [`doc_lint.py`](../../tools/doc_lint.py) by hand before every commit, **and** put a GitHub check back | **none**, same reason — [`gemini-cli/README.md`](gemini-cli/README.md) carries the same two steps | **none**, same reason — [`grok-build/README.md`](grok-build/README.md) carries the same two steps, plus the note that whoever verifies the hooks reference should wire this one and record it in [LEDGER.md](LEDGER.md) |
| `reply-gate.sh` | `UserPromptSubmit`: prints the `reply` gate's practices and each source's hard reply requirements at the START of the turn, which is the only moment before the reply that a hook can reach | **none** — no prompt-submit invocation point, so the gate's requirements never reach the reply they are about | **none**, same reason | **none as written**, same reason |
| `stop-git-check.sh` | `Stop`: blocks ending a turn with uncommitted, untracked or unpushed work, and runs the blocking half of the reply check against the session transcript | **none** — no teardown invocation point ([README.md](README.md)'s adapter table, `Teardown check` column). Note the second half would not transfer even if there were one: the reply check reads a transcript path the harness hands the hook, and a harness that hands its stop hook nothing gets the print without the enforcement | **none**, same reason | **none**, same reason |
| `precedent-individual-bootstrap.sh` | `SessionStart`: clones THIS account's private individual practice source, before the first turn, using an environment credential — the one route that beats `add_repo`'s per-session ordering | **none, and not for the usual reason.** The logic is harness-neutral ([`tools/precedent_source_bootstrap.py`](../../tools/precedent_source_bootstrap.py)); what cannot travel is the per-account URL, which [source-naming](../../practices/source-naming.md) keeps out of every tracked file. `tools/bootstrap.sh` clones the declared TEAM sources and stops there. On codex the individual set is a manual step | **none**, same reason | **none**, same reason |
| `settings.json` permission allowlist | Pre-approves the routine read-only and engine commands so a session is not stopped for each one | **none found** — [README.md](README.md)'s adapter table records `n/a`, and no codex equivalent was found in the research pass behind it | **none found**, same | **unresearched** — [`grok-build/README.md`](grok-build/README.md)'s Pre-approved-commands bullet says so in those words rather than asserting an absence nobody checked |
