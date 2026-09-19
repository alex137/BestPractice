---
slug:              todo-2026-09-07-loader-comment-names-an-unvendored-check
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
noted:             2026-09-07
closed:            2026-09-11
---
## What

- <a id="loader-comment-names-an-unvendored-check"></a>**The generated loader block
    tells every source set that a check catches drift, in exactly the repos where that
    check does not exist.** [tools/build_views.py](../tools/build_views.py) writes `do not
    hand-edit this block, tools/verify_harness.py's regeneration check fails on drift.`
    into the generated block unconditionally. But `verify_harness.py` is deliberately
    not vendored into a SOURCE set —
    [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) says so twice,
    each time as a known consequence it is working around. So the one line telling a
    session the block is protected is false in every private set, and it is the line a
    session reads instead of checking.

    **This is [precedent_check.py](../tools/precedent_check.py)'s own finding, one level
    up.** That module exists because `checked_by:` was "a claim: a string naming a script
    that existed", and its header states the principle: *"A claim nobody tested is worth
    less than no claim, because it reads as coverage."* A generated comment naming a
    check that cannot run in the repo it is generated into is the same shape, in a
    comment rather than a frontmatter field, and nothing tests it either.

    **Evidence, found 2026-09-07 in the team set.** `AGENTS.md`'s occasion index and
    `MAP.md` had been stale since `b9fae5a` rewrote `fail-gracefully`'s `occasion` and
    `index_clause` without regenerating. Nothing reported it; it was caught by hand, by
    running `build_views.py` for an unrelated practice edit and reading the diff.
    Verified identical in all three private sets: each carries the same generated line,
    none has `tools/verify_harness.py`.

    **Two fixes, and they are not the same size.** The honest one is to make the comment
    conditional — name `verify_harness.py` only where it is vendored, and elsewhere say
    plainly that regeneration is on the author and nothing here checks it. The better one
    is to make the claim true: `build_views.py` is deterministic and idempotent (verified
    — a second run on a clean tree is a no-op), so "regenerate into a temp dir and diff"
    is a cheap check, and `precedent_check.py` is now vendored into source sets and could
    host it. That one is not free: that registry is deliberately one entry per *enforced
    practice*, each owing a failure message that IS some practice's `## Rule` and a test
    that proves it fires. A regeneration check owns no practice, so it needs either a
    practice to belong to or a considered exception to that shape — which is a design
    call, not a fix. **Recommend doing the honest one now and filing the better one
    separately**, rather than letting a comment stay false while the design question
    is open.

    **Closed 2026-09-11 — the honest fix landed, and it is better than
    "say plainly that nothing checks it".** Both headers now name
    `python3 tools/build_views.py --check`: the same file that writes the
    view, so it exists wherever the view does, and it exits 1 on drift and 0
    clean (two-direction tested in a real individual set before wiring).
    Adopters also get a CI gate that runs it —
    `templates/github-actions/views-drift.yml.template` (since removed; folded into `precedent-check.yml.template`),
    installed into every new set by
    [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
    and named as missing by its `--verify` for the sets that predate it.

    **What the work found, and it changes this item's "better fix" half:**
    `precedent_check.py` already hosts exactly the check this item wished
    for — `generated-artifact-provenance` runs `build_views.py --check` as a
    subprocess — and it is inert in every source set. Measured 2026-09-11 in
    a real individual set: `--only generated-artifact-provenance` reports
    `1 skipped`, because `precedent_check.py` skips any check whose practice
    is not in force in the repo it runs in, and a source set's `practices/`
    holds only its own practices, never the universal one that check belongs
    to. So the design question is not where to host a regeneration check; it
    is [`provenance-check-skips-in-a-source-set`](todo-2026-09-11-provenance-check-skips-in-a-source-set.md)
    below, which is a bigger question than this item was.

## How It Closes

Already closed 2026-09-11 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
