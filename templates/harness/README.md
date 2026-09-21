# Harness adapters

The practice layer is agent-agnostic: everything operates on git + markdown +
plain Python, and the canonical instructions file is **`AGENTS.md`**
([../AGENTS.md.template](../AGENTS.md.template)), which several agent CLIs
read natively. What differs per harness is only the *wiring* — which filename
gets auto-loaded, how the bootstrap script gets run at session start, and
whether routine commands can be pre-approved. Each subdirectory here is that
wiring for one harness; a repo can install **more than one adapter side by
side**, so different agents can work the same repo under the same contract.

| Adapter | Instructions file | Bootstrap | Teardown check | Pre-approved commands |
|---|---|---|---|---|
| [claude-code/](claude-code/) | `CLAUDE.md` → one-line import of `AGENTS.md` | SessionStart hook (automatic) | Stop hook: blocks ending a turn with uncommitted, untracked, or unpushed work, and fires the `reply` gate | `settings.json` allowlist |
| [codex/](codex/) | `AGENTS.md` read natively | environment setup script | n/a | n/a |
| [gemini-cli/](gemini-cli/) | `GEMINI.md` → pointer to `AGENTS.md` | instructions-file directive | n/a | n/a |
| [grok-build/](grok-build/) | `AGENTS.md` read natively | `.grok/hooks.json` lifecycle hook (exact syntax unverified as of 2026-09-17 — see the adapter's own README before relying on it) | n/a | n/a |

**THE MARKDOWN LINT IS NO LONGER A GITHUB CHECK.** Since 2026-09-21 it
runs as `.claude/hooks/doc-lint-gate.sh`, which refuses a `git commit`
whose staged Markdown fails it. **Only Claude Code runs that hook**, and
the workflow it replaced is retired — so on every other adapter in this
table, nothing is checking Markdown before it reaches a shared branch.

**IF YOUR HARNESS HAS NO HOOKS, YOU NEED THE GITHUB CHECK — READ THIS
BEFORE SKIPPING IT.** The Markdown lint left GitHub Actions on 2026-09-21
and was replaced by `.claude/hooks/doc-lint-gate.sh`, which refuses a
`git commit` whose staged Markdown fails `doc_lint.py`. **That is
a Claude Code mechanism.** Read the Bootstrap and Teardown columns above:
every other adapter in this table says `n/a` or carries an unverified
lifecycle hook, which means **nothing checks your Markdown at all** unless
you put a check back in CI yourself.

So, on any harness other than Claude Code:

1. **Run the light check by hand before every commit** —
   `python3 tools/doc_lint.py <the markdown you touched>` — and
   treat that as non-optional rather than a nicety. Your harness will not
   remind you.
2. **Also turn the GitHub check on**, because step 1 is a habit and habits
   are what the hook exists to replace. Copy
   [github-actions/light-check.yml.template](../github-actions/light-check.yml.template)
   to `.github/workflows/light-check.yml` and set its `CUSTOMIZE` command
   to `python3 tools/doc_lint.py`, with its `paths:` list set to
   `"**/*.md"`. One job, checked when a pull request opens and when it
   lands.
3. **Enable Actions for the repository** if it is off — repository
   **Settings → Actions**. A workflow file in a repository with Actions
   disabled is a check nobody is running and nobody can see is not running
   ([documentation/GITHUB_ACTIONS.md](../../documentation/GITHUB_ACTIONS.md)).

**Doing 1 without 2 is the arrangement that just failed here.** "A session
is supposed to run it" was written down and followed for months, and still
nothing refused a commit that skipped it — which was only safe while CI was
behind it. Do not recreate that gap on a harness with even less enforcement
than the one that had it.

**A practice SOURCE set installs the claude-code adapter too, and until
2026-09-20 none did.** The table above reads as wiring a *consuming* repo
puts in — and a set publishes practices rather than installing them, so
nobody ever asked which filename the harness auto-loads in one. All four
sets alive on that date had `AGENTS.md` and no `CLAUDE.md`, and loaded their
own rules only because Claude Code falls back to `AGENTS.md` where a project
has no `CLAUDE.md` of its own. A set needs the stub and
[`hooks/precedent-universal-catalogue.sh`](claude-code/hooks/precedent-universal-catalogue.sh);
what it does not need is an `@import` of the catalogue that hook renders —
[`../../spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md`](../../spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md)
says why, and it is the same file a session should read before changing what
any hook here prints to stdout.

**WHAT CLAUDE CODE DOES THAT THE OTHER THREE DO NOT, mechanism by
mechanism: [PARALLELS.md](PARALLELS.md).** The table above answers "how is
each adapter wired"; that one answers "what does the person on this harness
not get", which is a different question and the one that goes stale
unwatched. It is checked by `claude-only-surface-has-a-parallel` — every
hook in `.claude/hooks/` must have a row with a verdict in all three
columns — and re-judged, rather than merely counted, on every
[very deep check](../../practices/very-deep-check.md).

**The Bootstrap column above is a real parallel only since 2026-09-21.** It
has named [`../../tools/bootstrap.sh`](../../tools/bootstrap.sh) as the
harness-neutral equivalent of Claude Code's `SessionStart` hook since this
directory existed, and for all that time the script ran three of the hook's
seven steps. What the other three adapters were therefore never given: the
declared team sources cloned, those sources refreshed, and
`.precedent/SESSION_PRACTICES.md` written — the file this repo's own
Standing instruction tells **every** session to read, carrying every team
and individual practice in force. A codex session read that instruction,
found no file, and worked with none of them. Nothing in this README was
false; the hook and the script had simply never been read side by side,
which is now a standing item in the very deep check's pass 1.

**Enforcement caveat.** Adapters with a hook mechanism give *hard* guarantees
(bootstrap always runs); adapters without one rely on the agent following the
instructions file — a *soft* guarantee. The audits partially compensate: a
skipped convention still fails loudly when the audit runs at commit/merge
time. This is why practice `convention-to-audit` (conventions become scripts) is the load-bearing
practice in a multi-agent repo.

Using a harness not listed here? The recipe is six questions: (1) what
filename does it auto-load — add a pointer file to `AGENTS.md`; (2) does it
have a session-start hook — wire `tools/bootstrap.sh` into it, else rely on
the instructions-file directive; (3) does it have a stop/teardown hook that
can block ending a turn — port the git-hygiene check, the `reply`-gate print
and the blocking reply check
([claude-code/hooks/stop-git-check.sh](claude-code/hooks/stop-git-check.sh))
if so, and note that the blocking half needs the hook to be handed the
session's own transcript: `tools/precedent_reply_check.py` reads the path
Claude Code passes it, and a harness that hands its stop hook nothing has
the print and not the enforcement; (4) can commands be pre-approved — port the allowlist idea if so;
(5) does it run something when the person submits a prompt — port
[claude-code/hooks/reply-gate.sh](claude-code/hooks/reply-gate.sh), which is
the only moment the `reply` gate reaches the reply it is about; (6) can it
run something before a tool call — port the freshness gate
([claude-code/hooks/freshness-guard.sh](claude-code/hooks/freshness-guard.sh)),
and wire its session-start half plus
[claude-code/hooks/commit-identity.sh](claude-code/hooks/commit-identity.sh)
into whatever answer question (2) gave, since neither depends on anything
Claude Code specific beyond how it is invoked.

The freshness gate also reads `PRECEDENT_FRESHNESS_ALSO` from the
environment — `;`-separated `<path>=<base branch>` entries for repositories
the session merely has **attached**. That part is not harness-specific at
all: a hook fires for the project dir and nothing else, so an attached
sibling clone runs none of its own freshness checking no matter which
harness is in play, and an adapter that ports the gate should read the
variable too. Unset, it changes nothing. A ported gate must **expand `~`,
`$HOME` and `$CLAUDE_PROJECT_DIR` in each path**: nothing expands a value
read back out of a variable, and `$HOME` differs between containers, so the
unexpanded form names nothing on half the machines it runs on.
Then contribute the adapter back upstream.

**A practice SOURCE's adapters can travel mechanically, since 2026-09-12.**
Everything above is about the adapter templates in this directory, which a
repo installs by hand. A practice source (an individual or team set) that
ships its own `bootstrap/*.sh` no longer needs that step: it declares each one
in its own `precedent.json`, and
[tools/precedent_materialize.py](../../tools/precedent_materialize.py)
installs it into every consuming repo on the same sync that carries the
practices and checks, recording the copy in that repo's `MANIFEST.json` so a
later hand-edit shows up as drift. The settings wiring still does not travel
and is refused as a destination — each repo substitutes its own base branch
there. See [spec/SOURCES.md](../../spec/SOURCES.md)'s "Harness adapters travel
with the source" for the two incidents behind it and the decisions taken.

**Transfer verdicts for changes to any one adapter are ledgered:**
[LEDGER.md](LEDGER.md) — a change to one member presumptively transfers to
the others, and this family's ledger records the per-member verdict for
each change rather than leaving it to a headline judgment call
([parallel-artifact-ledger](../../practices/parallel-artifact-ledger.md)).
