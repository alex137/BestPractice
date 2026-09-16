---
slug:              todo-2026-09-14-set-cannot-show-a-universal-practice
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
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="set-cannot-show-a-universal-practice"></a>**In a practice SET,
    `precedent_show.py SLUG` cannot read any universal practice — and the
    generated file that delivers those practices tells its reader to run
    exactly that command.** Measured 2026-09-14 in a real team set, not
    reasoned about: `python3 tools/precedent_show.py fixture-owns-its-state`
    exits 1 with *"unknown slug(s), no practices/\*.md file for"*, while
    line 354 of that set's own `.precedent/SESSION_PRACTICES.md` — generated
    minutes earlier by [precedent_session_practices.py](../tools/precedent_session_practices.py),
    listing 111 universal practices as binding — says *"run `python3
    tools/precedent_show.py SLUG` for each listed slug to load its Rule."*
    **Why it works in a consumer and not in a set.**
    [precedent_show.py](../tools/precedent_show.py) reads one directory,
    `<root>/practices/`. In a consumer repo that directory is a
    [precedent_materialize.py](../tools/precedent_materialize.py) snapshot
    holding every resolved source, so every slug is there. A set deliberately
    does not materialize universal — that is shape 3 in
    [spec/SOURCE_SET_PROSE_GAP.md](../spec/SOURCE_SET_PROSE_GAP.md), approved
    2026-09-13, and the untracked `.precedent/SESSION_PRACTICES.md` is what
    replaced the committed copy. So a set's `practices/` holds only its own.
    **What DOES arrive at a set is narrower than it looks**, which is the
    part worth writing down. The occasion index reaches it (one line per
    practice) and the RESIDENT universal practices reach it in full, because
    both are baked into the generated block. Everything else — Rule, Detail,
    Why, Story for the ~100 on-demand universal practices — is unreachable
    from a set by any documented command.
    **Fix shape:** have `precedent_show.py` fall back to the resolved
    sources' own `practices/` directories when a slug is not in `<root>`, and
    name the level it came from in the output.
    [precedent_resolve.py](../tools/precedent_resolve.py) has been in
    `ENGINE_FILES` since 2026-09-13, so a set already carries what this needs.
    **Out of scope when found, not blocked:** it surfaced at the tail of an
    unrelated relayed note, and fixing it is engine work that has to be rolled
    to four sets before it helps anyone — a bigger piece than the note asked
    for. Nothing is waiting on a decision.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
