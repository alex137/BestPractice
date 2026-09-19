---
slug:              todo-2026-09-06-build-codeowners-check-flag
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-06
---
## What

- <a id="build-codeowners-check-flag"></a>~~**`build_codeowners.py --check` is not a check — it takes no such flag
    and writes anyway.**~~ **Done 2026-09-06.** Both defects fixed in
    [tools/build_codeowners.py](../tools/build_codeowners.py): a real `--check`
    that compares and exits non-zero without writing (and an unknown flag is
    now refused rather than falling through to the destructive path — that
    fall-through was the bug, and doing the destructive thing on a typo is
    how it stayed hidden), and the derived-file header now stamps a sha256 of
    `approvers.json`'s own content instead of `git rev-parse HEAD`, so an
    unchanged approver list regenerates byte-identically. Harness-tested with
    10 stated cases, including negative controls, in
    `check_codeowners_check_is_a_check`. BestPractice has no `approvers.json`
    of its own, so the fixture supplies one — that absence is exactly why
    this went unnoticed while the tool was private to one team set.
    **Cross-source consequence, not yet rolled out
    ([cross-source-rollout](../practices/cross-source-rollout.md)):** the header
    format changed, so the first regeneration in each team set produces a
    one-time diff. Expected and correct — after it, `--check` is stable.
    **Blocked on:** `themorgan/precedent-team-repo-maintenance` not attached this
    session (`themorgan/precedent-team-tms` was also named here until it was
    retired 2026-09-10). It needs
    `python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`
    then `python3 tools/build_codeowners.py`, committed.

## How It Closes

Already closed 2026-09-06 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
