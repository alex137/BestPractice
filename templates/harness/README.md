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

**Enforcement caveat.** Adapters with a hook mechanism give *hard* guarantees
(bootstrap always runs); adapters without one rely on the agent following the
instructions file — a *soft* guarantee. The audits partially compensate: a
skipped convention still fails loudly when the audit runs at commit/merge
time. This is why practice `convention-to-audit` (conventions become scripts) is the load-bearing
practice in a multi-agent repo.

Using a harness not listed here? The recipe is four questions: (1) what
filename does it auto-load — add a pointer file to `AGENTS.md`; (2) does it
have a session-start hook — wire `tools/bootstrap.sh` into it, else rely on
the instructions-file directive; (3) does it have a stop/teardown hook that
can block ending a turn — port the git-hygiene check and the `reply`-gate
print
([claude-code/hooks/stop-git-check.sh](claude-code/hooks/stop-git-check.sh))
if so; (4) can commands be pre-approved — port the allowlist idea if so;
(5) can it run something before a tool call — port the freshness gate
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
