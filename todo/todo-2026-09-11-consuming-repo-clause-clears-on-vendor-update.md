---
slug:              todo-2026-09-11-consuming-repo-clause-clears-on-vendor-update
kind:              verify
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-11
closed:            null
---
## What

- <a id="consuming-repo-clause-clears-on-vendor-update"></a>**Confirm the
    consuming repo's `Source:` clause actually clears, rather than assuming
    it.** The clause-matcher faults in item 66's sibling fix were found from a
    consuming repo, whose generator emits a hyphenated `Source:` path. That
    repo kept the clause in place while it still failed, on the grounds that
    it was correct and a reader could use it, so its
    `generated-edit-goes-upstream` violation should clear on its next vendor
    update with no edit on its side. The regex accepts that clause shape now —
    asserted as a harness case — but whether the path it names resolves in
    that repo's own tree is a fact about that tree.
    **Blocked on a session rooted in that repository:** it is under a
    different owner, and `add_repo` refuses cross-owner, so nothing here can
    read it. One command there answers it:
    `python3 tools/precedent_check.py --only generated-edit-goes-upstream`
    after the vendor update.
    **Disposition:** wait (2026-09-11 — no session has set this to `ask`)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
