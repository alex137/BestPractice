---
slug:              todo-2026-09-11-figures-reach-commit-messages-ungated
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
noted:             2026-09-11
closed:            null
---
## What

- <a id="figures-reach-commit-messages-ungated"></a>**A figure can reach a
    commit message without anything checking it, and it did twice in two
    days.** Every script-derived number in a *document* sits inside a
    generated block that [doc_sync.py](../tools/doc_sync.py) regenerates and
    compares
    ([computed-numbers-in-scripts](../practices/computed-numbers-in-scripts.md)).
    **A commit message has no such gate, and by construction cannot easily
    have one**: it is written after the checks have run, nothing reads it
    afterwards, and once pushed to a shared branch it is published history
    that [no-rewrite-for-warnings](../practices/no-rewrite-for-warnings.md)
    forbids correcting in place. The correction has to live somewhere else —
    a comment on the pull request — where a reader of the commit will not
    see it.
    **Two instances, both 2026-09-11.** A session reported a continuous
    integration job as hanging "after 18 minutes", a duration it got by
    comparing a timestamp against a present moment it had never measured;
    that one is a live gotcha in [AGENTS.md](../AGENTS.md). Then the merge
    commit for
    [PR #228](https://github.com/alex137/BestPractice/pull/228) said the
    gotchas section dropped to "8,988 tokens" when the measured figure was
    9,015 — a number true of a tree that had existed earlier in the same
    session, restated at merge time as though quoting rather than asserting.
    **That is the shape worth naming: the failure is not inventing a number,
    it is re-using a real one after the thing it described has changed.**
    [no-invented-specifics](../practices/no-invented-specifics.md) does not
    distinguish the two, and neither did the session.
    **Why this is queued rather than done, and why it is a weak item.**
    [checkable-gets-checked](../practices/checkable-gets-checked.md) asks for a
    mechanical check before anything is left advisory, so the obvious one was
    measured rather than assumed: flagging bare numerals in commit messages
    across the last 80 non-merge commits here matches **304 numbers in 54 of
    them — 67%**. A gate firing on two thirds of commits is not a gate. The
    numbers it would catch are overwhelmingly legitimate (counts of stated
    cases, check tallies, dates, byte sizes), and the ones that matter — a
    before/after delta re-stated from memory — are indistinguishable from
    them by shape alone. **So the naive check is ruled out by measurement,
    and no better one has been designed.** It may be that the honest answer
    is "keep figures out of commit messages and put them in the pull-request
    body, where the document gates reach", which is a convention change
    rather than a check, and a real cost of its own — commit messages are
    where this project deliberately records what was measured.
    **Nobody should treat this item as ripe.** It names a real, twice-observed
    failure and does not have a remedy worth adopting; it is filed so the
    third instance lands against a record instead of being discovered fresh.
    **Do not close it by writing an advisory practice** — that is the outcome
    [checkable-gets-checked](../practices/checkable-gets-checked.md) exists to
    make a session argue for, and the argument has not been made.
    **Approval:** Morgan, 2026-09-11, `strength: assented` — he asked for the
    item and said in the same breath that it is a weak one.
    **Disposition:** wait (2026-09-11, Morgan — a session did not set this to `ask`; he is the one it waits on)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
