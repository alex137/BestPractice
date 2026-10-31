---
slug:              todo-2026-09-08-retired-practice-filenames
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan -- whether to close it as evaluated"
noted:             2026-09-08
closed:            null
---
## What

- <a id="retired-practice-filenames"></a>**Evaluate marking retired and deduplicated practice files in
  their filename, so a directory listing shows what is still in force.**
  Morgan, 2026-09-08, raised it as e.g. `retired.practice-name-here.md` —
  sortable, skippable, and it stops a listing of `practices/` reading as
  the live catalogue when part of it is not.

  **Why it was not done that day**, and both halves of the argument are
  worth keeping because the next session will re-derive one of them:

  - *Against.* Practice files cite each other by bare filename, and those
    links **travel into every consuming repo**, where nobody can repoint
    them ([rename-updates-links](../practices/rename-updates-links.md) cannot
    reach across a repository boundary).
    [spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md) already rejected a
    `retired/` directory on the same ground, plus two more: it puts the
    fact in two places (a path *and* a `status:` field) with nothing
    deciding which wins, and it hides withdrawn rules from the `grep`
    someone doing prior-art research actually runs.
  - *For.* The listing problem is real. The counter-argument assumes people
    read [MAP.md](../MAP.md), whose generated **"Withdrawn practices"** table
    already carries status, successor and the reason each was withdrawn —
    strictly more than a filename prefix could. If the raw directory is
    where people actually look, that table is not reaching them.
  - *Morgan's fallback, and why it is worse rather than better:* renaming
    during [very-deep-check](../practices/very-deep-check.md) instead of in
    real time. It is the same breakage on a delay, and it puts a rename
    sweep inside a check whose whole discipline is to report and let a
    person decide.

  **The cheaper thing to try first**, if the trigger is a raw listing:
  surface `status:` in `precedent_show.py`'s output and make MAP.md's
  withdrawn table easier to find. That costs nothing and breaks nothing.

  **Disposition:** wait

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
2026-10-31, very deep check of 2026-10-30, pass 4 (ambiguous, asked of Morgan): the cheaper
thing this item said to try first is in place. `precedent_show.py` opens a
withdrawn practice with "NOT IN FORCE ANYWHERE (status: ...)" (since
284b4cf4, 2026-09-06), and MAP.md carries the "Withdrawn practices" table.
Nothing since has shown a raw listing misleading anyone. The session would
close it as evaluated, keeping the filenames as they are.
