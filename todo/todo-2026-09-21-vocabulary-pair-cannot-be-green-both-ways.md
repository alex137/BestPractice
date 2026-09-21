---
slug:              todo-2026-09-21-vocabulary-pair-cannot-be-green-both-ways
kind:              manual
domain:            tooling
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

**[`doc_sync.py`](../tools/doc_sync.py)'s vocabulary pair cannot be green in a session with private
sources attached AND in CI at the same time.** The generated block in
[documentation/DAILY_HABITS.md](../documentation/DAILY_HABITS.md) is
rendered from `tools/precedent_vocabulary.py --emit vocabulary`, which
collects the `command:` field of every practice in every **resolved**
source — and which sources resolve is a property of the session, not of the
repository.

Measured 2026-09-21, same tree, same commit:

| Context | Rows the script emits |
|---|---|
| This session (individual source attached) | 21, including `So what?` (`so-what-test`, individual) |
| `PRECEDENT_USER_CONFIG` pointed at nothing, as in CI | 20 |

The committed document has the 20. So `computed-numbers-in-scripts`
**violates in every session that resolves a private source carrying a
command**, and passes in CI. Running `doc_sync.py --write` to clear it
would commit the 21-row block, which flips the failure to CI and, worse,
publishes an individual source's command text into the public upstream
repository.

## Why it matters beyond the red check

A gate that can only be cleared by publishing private content is a gate
pushing every session toward a leak. Nobody has done it yet because the
fix looks unappealing, not because anything stops it —
[tools/leak_gate.py](../tools/leak_gate.py) would pass the row, since the
text carries no private repository name.

## What would close it

Three shapes, none of them obviously right, which is why this is filed
rather than fixed:

1. **Render only universal rows into the public document**, and let each
   private source render its own commands into its own surface. Keeps the
   public page stable in every context; loses the "one list of everything
   in force" property the `Vocabulary` command has.
2. **Drop the pair from [`doc_sync.py`](../tools/doc_sync.py)'s `PAIRS`** and let that page be
   hand-maintained with a pointer to `python3 tools/precedent_vocabulary.py`
   for the live answer, the same reasoning that keeps the branch report out
   of `PAIRS` (its output depends on the moment it runs, not on the tracked
   tree).
3. **Declare the pair session-dependent** and teach the check to compare
   against the universal-only render, whatever the session resolves.

Found while running the deep check before landing the very-deep-check
deepening work (2026-09-21). Not caused by it, and not fixed by it: the
choice between those three is a decision about what the public repository
publishes, which belongs to Morgan.
