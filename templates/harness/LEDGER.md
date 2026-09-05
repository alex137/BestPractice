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
| 2026-09-01 | [`969be87`](https://github.com/alex137/BestPractice/commit/969be87c8ad9268795276febe7c597d274e515bd) — an accidental merge of Alex's own in-progress branches added scaffolding to all three adapters, then was reverted the same session as an authorization mistake unrelated to the content's merit | reverted; no transfer verdict applicable — the content never actually landed as this repo's own decision | reverted, same as claude-code | reverted, same as claude-code |
| 2026-09-03 | [`0980ae3`](https://github.com/alex137/BestPractice/commit/0980ae3bf051a97ac0fb5aecc70e7e6590fb0163) — wired the path-triggered loading channel into a `PreToolUse` hook | applied as `hooks/precedent-paths.sh`, wired into `settings.json`'s `PreToolUse` (matcher `Edit\|Write\|NotebookEdit`) | no transfer because codex has no hook mechanism to wire it into, same reason as the Stop hook rows above | no transfer, same reason as codex |
| 2026-09-04 | [`36dbeb9`](https://github.com/alex137/BestPractice/commit/36dbeb90e18ffa222c5fca117d00a23ae6feed43) — the gate-channel audit found `reply` cited as firing "at the stop hook" but never actually wired there | applied: `hooks/stop-git-check.sh` now also fires `tools/precedent_gate.py reply` before blocking on git hygiene | no transfer because codex has no teardown/stop-hook mechanism (same as the row above) — `reply` stays cited-only there, by design, not by omission (the commit's own stated reasoning) | no transfer, same reason as codex |

**Mechanically audited as of 2026-09-05**: `tools/precedent_check.py`'s
`parallel-artifact-ledger` check (`checked_by` on
[the practice file](../../practices/parallel-artifact-ledger.md)) walks
`git log --no-merges` for each member directory and fails if any commit's
hash isn't referenced somewhere above — the "audit that fails any change
date lacking a complete row" the practice's own Rule names. Found four
real backfill gaps on its first run (the three rows above added 2026-09-05,
plus the reply-gate row added 2026-09-04 the day before the audit existed)
— this file's own retroactive backfill from 2026-09-04 had missed them.
What it does not check: whether a recorded verdict is *correct*, only that
a row exists.
