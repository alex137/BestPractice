---
slug:              todo-2026-09-13-reply-check-rollout
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
noted:             2026-09-13
closed:            null
---
## What

- <a id="reply-check-rollout"></a>**Roll the blocking reply check out to the
    sources that want one, and land the individual set's half.** Built
    2026-09-13 in this repo: `tools/precedent_reply_check.py` enforces whatever
    a source declares in a `reply_check.json` at its root, and the `reply` gate
    now serves every source rather than this repo's own `practices/` alone.

    **The individual half LANDED, and this item said otherwise until
    2026-09-14.** Verified by content that day, not inferred: the set's
    `reply_check.json` is on its `origin/main`, declaring
    `require_heading_matching: "next step"` and the two archive sentences, and
    it is what gates every reply in a session that resolves it — including the
    session that checked. The paragraph below describes the state on
    2026-09-13 and is kept as the record of what was true then.
    **DECIDED 2026-09-14: the individual half is CLOSED on its stated
    condition, and only the engine-rollout half stays open.** Morgan took the
    recommendation as written — *"let's implement your recommendation"* — with
    no argument for it, so **strength: assented (2026-09-14, Morgan)**. The
    stated condition was that the individual set carry a `reply_check.json`
    declaring the heading pattern and the two closing sentences: it is on that
    set's `origin/main`, and it gated the reply of the session that checked,
    which is the condition met rather than resembled. What is
    genuinely left is that the four attached sources still run an older
    vendored engine, so none of them can declare a CONDITIONAL requirement of
    its own — the object-vs-list form and
    `require_when_context_grew_tokens`. That is ordinary vendor-update work,
    not a design question, and it belongs to whichever session is rolling the
    sets forward rather than to a separate effort.

    **The individual set's half was written and could not be pushed from here.**
    Its `next-steps-after-commit` gained the session-disposition clause, its
    `## Install` was corrected (it asserted a mechanical check was impossible,
    which was the premise that stopped anyone building one), and a
    `reply_check.json` declares the heading pattern and the two closing
    sentences. All three are edits in a clone this session can read and not
    write: `git push --dry-run` returns *"access denied by the git proxy ... not
    in this session's authorized repository set"* and HTTP 403, measured
    2026-09-13, and `add_repo` refuses cross-owner. The route is a session
    rooted under that owner, seeded with the text — the same route
    [`attach-private-sources`](todo-2026-09-06-attach-private-sources.md) names.

    **The engine half reaches a source only when its vendored copy refreshes**
    (`python3 tools/precedent_refresh_sources.py --apply`). Until then an
    attached source's own `precedent_gate.py` still reads one directory and its
    hooks have no reply check to call — and all four attached sources were
    already behind at this session's start, so nothing about this change made
    them stale.

    **The universal source now declares one too, 2026-09-14** — one
    requirement, the compaction offer from
    [session-spend-follows-the-task](../practices/session-spend-follows-the-task.md),
    fired by context growth rather than unconditionally. Two engine changes
    came with it and both are backwards-compatible: a
    [`reply_check.json`](../reply_check.json) may
    now be a LIST of requirements as well as a single object, and a
    requirement may carry `require_when_context_grew_tokens`. **An attached
    source keeps working on its old vendored engine** — its object-form file
    reads exactly as before — but a source that wants a *conditional*
    requirement of its own needs the refreshed engine first, which is the
    paragraph above. Not rolled out to the four attached sources in the
    landing session on purpose: all four were already ≈249 commits behind, so
    refreshing them is a vendor update with its own runbook and its own
    authorization ([vendor-update-runbook](../practices/vendor-update-runbook.md)),
    not a rollout of this change.

    **What each other source has to decide, and nobody should decide for it:**
    whether it wants a `reply_check.json` of its own. A team set declaring one
    imposes a closing convention on everyone in that team, which is a real
    decision and not a default; the engine's behaviour with none declared is to
    check nothing at all.

    **A session is already seeded with the individual set's half**, rooted in
    that repository, created 2026-09-13:
    [session_01GuoULzeTym1XFPyTxird4T](https://claude.ai/code/session_01GuoULzeTym1XFPyTxird4T).
    Its prompt carries the full text of all four edits and the JSON, because
    nothing else can carry them — the text is private and cannot be staged in
    this public repository, and a cloud session cannot be messaged after it
    starts (the gotcha about a spawned session losing its tools mid-run is the
    same constraint from the other side). If that session is gone before
    anyone opens it, the text has to be rebuilt from this item plus the
    practice's own history.

    **blocked-on:** the four attached sets still running the `c3c78d9` engine.
    Refreshing them is vendor-update work inside those repositories, with its
    own runbook and its own authorization, and the sessions doing those
    rollouts own it — there is nothing here to hand anyone.
    **Disposition:** wait (2026-09-14) — the 2026-09-13 `ask` was there because
    the written individual half would die with that container; it did not, it
    landed, and nothing left in this item needs Morgan.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
