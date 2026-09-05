# Harness adapter family — transfer ledger

Practice: [parallel-artifact-ledger](../../practices/parallel-artifact-ledger.md).
The family: [claude-code/](claude-code/), [codex/](codex/), and
[gemini-cli/](gemini-cli/) are one design (the practice layer's harness
wiring) in three parallel forms — see [README.md](README.md) for what each
adapter actually is. A change to the mechanism inside one presumptively
transfers to the others; this table records, per change, the verdict for
each member — *applied as `<what>`*, or *no transfer because `<reason>`* —
so a headline-level "this one's harness-specific" call can't silently skip
a mechanism that should have propagated. Origin incident:
[parallel-artifact-ledger](../../practices/parallel-artifact-ledger.md)'s
own `## Story`. Add a row here in the same commit as any change to a
member's wiring, before this file existed retroactively for the one already
in the tree.

| Date | Originating change | claude-code | codex | gemini-cli |
|---|---|---|---|---|
| 2026-08-29 | [`9de83a2`](https://github.com/alex137/BestPractice/commit/9de83a283735da32985142bbbb3e3239cf68737f) — Stop hook blocking a turn end with uncommitted/untracked/unpushed work | applied as `hooks/stop-git-check.sh`, wired into `settings.json`'s `Stop` hook | no transfer because codex has no teardown/stop-hook mechanism to wire it into (per [README.md](README.md)'s adapter table — a soft-guarantee harness, not a decision left open) | no transfer because gemini-cli has no teardown/stop-hook mechanism either, same reason as codex |
| 2026-09-04 | [`36dbeb9`](https://github.com/alex137/BestPractice/commit/36dbeb90e18ffa222c5fca117d00a23ae6feed43) — the gate-channel audit found `reply` cited as firing "at the stop hook" but never actually wired there | applied: `hooks/stop-git-check.sh` now also fires `tools/precedent_gate.py reply` before blocking on git hygiene | no transfer because codex has no teardown/stop-hook mechanism (same as the row above) — `reply` stays cited-only there, by design, not by omission (the commit's own stated reasoning) | no transfer, same reason as codex |

No mechanical audit wired yet — this practice is one of the catalogue's
genuinely resistant set (no `checked_by`; see
[spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md)'s enforcement
breakdown), so a missing row here is a routing-audit/full-practice-audit
finding, not (yet) a hard gate.
