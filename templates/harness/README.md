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
time. This is why practice 6 (conventions become scripts) is the load-bearing
practice in a multi-agent repo.

Using a harness not listed here? The recipe is four questions: (1) what
filename does it auto-load — add a pointer file to `AGENTS.md`; (2) does it
have a session-start hook — wire `tools/bootstrap.sh` into it, else rely on
the instructions-file directive; (3) does it have a stop/teardown hook that
can block ending a turn — port the git-hygiene check and the `reply`-gate
print
([claude-code/hooks/stop-git-check.sh](claude-code/hooks/stop-git-check.sh))
if so; (4) can commands be pre-approved — port the allowlist idea if so.
Then contribute the adapter back upstream.

**Transfer verdicts for changes to any one adapter are ledgered:**
[LEDGER.md](LEDGER.md) — a change to one member presumptively transfers to
the others, and this family's ledger records the per-member verdict for
each change rather than leaving it to a headline judgment call
([parallel-artifact-ledger](../../practices/parallel-artifact-ledger.md)).
