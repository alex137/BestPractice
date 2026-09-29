---
slug:              todo-2026-09-28-fix-moved-practice-mentions-in-two-sets
kind:              manual
domain:            vendoring
severity:          null
status:            open
disposition:       ask
remind_on:         "2026-09-28"
blocked_on:        "a Promote of BestPractice pre-staging to staging: precedent-individual's link check refuses its fixed links to fresh-before-write and dont-race-another-window until staging carries them"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-28
closed:            null
---
## What

**Run `precedent_move.py --mentions-only` for four earlier moves, in two
sets, and push the result to each set's `pre-staging`.** Moves made before
[tools/precedent_move.py](../tools/precedent_move.py) fixed mentions left
links and sentences in the old sets that still place the practice there.
A dry run over every earlier move found six files in two sets:

| Slug | From | Now lives in |
|---|---|---|
| `fresh-before-write` | precedent-individual | universal (this repo) |
| `dont-race-another-window` | precedent-individual | universal (this repo) |
| `content-directory` | precedent-individual | precedent-shared-working-style |
| `small-calls` | precedent-shared-working-style | universal (this repo) |

From a BestPractice checkout on `pre-staging`, with both sets checked out
on their own `pre-staging`:

    python3 tools/precedent_move.py --mentions-only --slug <slug> \
        --from <individual|shared> --from-path <old set> \
        --to <universal|shared> --to-path <. or the new set>

Then reword by hand the sentences the tool names (`reword by hand:`) --
the two known ones are `practices/name-the-branch.md` in
precedent-individual ("correct in this repository's own text", about
`fresh-before-write`) and `README.md` lines 22 and 33 in
precedent-shared-working-style (the practices table and "in this repo
shows the shape", both naming `small-calls.md`).

## Why

Morgan, 2026-09-28 (strength: decided), on moves leaving stale mentions
behind: "I don't need a detailed report but for those problems to be
solved." The tool fix landed in this repo; the two sets could not be
pushed from the session that wrote it (the git proxy refused both).

## Progress

**2026-09-28, run from a session with push access to both sets.**
precedent-shared-working-style is done: its fix is on its `pre-staging`
(`68acaf1`), and the `small-calls` dry run prints "nothing to fix".

precedent-individual's fix is committed (`e82312d`, saved on its branch
`claude/moved-practice-mentions`) but not on its `pre-staging`: its push
check refuses it under `practice-links-travel`. The tool points the links
at `blob/staging/practices/...` in this repo, and `fresh-before-write` and
`dont-race-another-window` exist only on this repo's `pre-staging` so far,
so those links would 404 today. The check is right. Once a Promote puts
both on `staging` (and the BestPractice clone beside the set is on a
branch that carries them), rerun its push check and fast-forward its
`pre-staging` to that commit.

## Closes when

Both sets' `pre-staging` carry the fixes, and a `--mentions-only --dry-run`
for each row above prints "nothing to fix".
