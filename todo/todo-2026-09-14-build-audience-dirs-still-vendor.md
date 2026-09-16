---
slug:              todo-2026-09-14-build-audience-dirs-still-vendor
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a judgment about the links, which is why this was left out of the change that prompted it rather than swept in. `philosophy/` is linked from a handful of vendored files and nothing more; [spec/](../spec/) is cited dozens of times from the vendored [INSTALL.md](../INSTALL.md) itself, and cutting it turns t"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="build-audience-dirs-still-vendor"></a>**Three more directories whose audience is "someone building Precedent"
    still vendor, and only `philosophy/` was cut.** Added 2026-09-14, when
    Morgan asked why the vendoring instructions were shipping `philosophy/`
    to adopters at all. The answer generalizes further than the fix did:
    [spec/DOCUMENT_LIFECYCLE.md](../spec/DOCUMENT_LIFECYCLE.md)'s placement
    table sorts directories by audience, and it puts [spec/](../spec/),
    `record/` and [decisions/](../decisions/) under *"a contributor or session
    building Precedent"* — the same audience test that took `evals/` out in
    the first place, and the same one that took `philosophy/` out now. An
    adopter vendors all three today and reads none of them.

    **Blocked on:** a judgment about the links, which is why this was left
    out of the change that prompted it rather than swept in. `philosophy/`
    is linked from a handful of vendored files and nothing more;
    [spec/](../spec/) is cited dozens of times from the vendored
    [INSTALL.md](../INSTALL.md) itself, and cutting it turns this repo's own
    install instructions into a document that points repeatedly at a
    directory the reader does not have. [tools/doc_lint.py](../tools/doc_lint.py)
    skips the link check inside a mirrored tree, so nothing would go red —
    which makes this worse, not better: the dead links would be invisible
    to every gate and visible to every reader. Either rewrite those
    citations as absolute upstream URLs first (the same move
    [practice-links-travel](../practices/practice-links-travel.md) already
    makes for the catalogue), or decide `spec/` earns its passage and cut
    only `record/` and `decisions/`.

    **Three more, measured 2026-09-14 by a by-the-book §1 rehearsal**: the
    vendored tree also carries this repo's `.github/workflows/` (three
    workflows GitHub never runs from a subdirectory), `.claude/` (this
    repo's own hook wiring) and `local/` — whose
    [merge-target-is-beta-branch](../local/practices/merge-target-is-beta-branch.md)
    tells every PR to target a branch the adopter's project does not have.
    A session grepping the adopter's repo for rules finds another
    repository's. 382 files and 128,000 lines landed in that install's one
    commit; `checkin.py not-vendored` reported `0 of 360` excluded because
    its exclusion list and §1 step 1's are the same two directories, so
    widening one means widening both and the harness check that ties them.

    **Disposition:** wait (2026-09-14, the session that cut `philosophy/`)

## How It Closes

Not open until: a judgment about the links, which is why this was left out of the change that prompted it rather than swept in. `philosophy/` is linked from a handful of vendored files and nothing more; [spec/](../spec/) is cited dozens of times from the vendored [INSTALL.md](../INSTALL.md) itself, and cutting it turns t

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
