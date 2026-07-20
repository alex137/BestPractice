# Harness adapters

The practice layer is agent-agnostic: everything operates on git + markdown +
plain Python, and the canonical instructions file is **`AGENTS.md`**
([../AGENTS.md.template](../AGENTS.md.template)), which several agent CLIs
read natively. What differs per harness is only the *wiring* — which filename
gets auto-loaded, how the bootstrap script gets run at session start, and
whether routine commands can be pre-approved. Each subdirectory here is that
wiring for one harness; a repo can install **more than one adapter side by
side**, so different agents can work the same repo under the same contract.

| Adapter | Instructions file | Bootstrap | Pre-approved commands |
|---|---|---|---|
| [claude-code/](claude-code/) | `CLAUDE.md` → one-line import of `AGENTS.md` | SessionStart hook (automatic) | `settings.json` allowlist |
| [codex/](codex/) | `AGENTS.md` read natively | environment setup script | n/a |
| [gemini-cli/](gemini-cli/) | `GEMINI.md` → pointer to `AGENTS.md` | instructions-file directive | n/a |

**Enforcement caveat.** Adapters with a hook mechanism give *hard* guarantees
(bootstrap always runs); adapters without one rely on the agent following the
instructions file — a *soft* guarantee. The audits partially compensate: a
skipped convention still fails loudly when the audit runs at commit/merge
time. This is why practice 6 (conventions become scripts) is the load-bearing
practice in a multi-agent repo.

Using a harness not listed here? The recipe is three questions: (1) what
filename does it auto-load — add a pointer file to `AGENTS.md`; (2) does it
have a session-start hook — wire `tools/bootstrap.sh` into it, else rely on
the instructions-file directive; (3) can commands be pre-approved — port the
allowlist idea if so. Then contribute the adapter back upstream.
