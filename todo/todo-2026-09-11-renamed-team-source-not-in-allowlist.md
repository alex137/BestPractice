---
slug:              todo-2026-09-11-renamed-team-source-not-in-allowlist
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a session that can write to the private individual source, and a decision about which of those two homes it belongs in."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-11
closed:            null
---
## What

- <a id="renamed-team-source-not-in-allowlist"></a>**Nothing checks that a
    rename carried its allowlist entry.** *(The anchor is kept and the title
    changed: anchors are permanent here
    ([rename-updates-links](../practices/rename-updates-links.md)), and this
    item's original claim — that the leak gate was red on
    `precedent-beta-v01` because the renamed team source had no allowlist
    entry — was **wrong**. What is left is the half that was right, and it is
    the more useful half.)*

    **What actually happened, 2026-09-11.** The gate reported `FAIL: 30
    hit(s)` and it was reading a **stale blocklist**. The allowlist line for
    the renamed source had landed in the private individual source at
    `549bccb` (16:19 -0300); the session that filed this item held a clone
    taken before that. Measured both ways against
    `precedent-beta-v01` at `17d261b`: with that file at `origin/main` the
    gate reports `OK, 944 unit(s) clean`; with the same file at its previous
    commit `3b1c73b`, `FAIL: 30 hit(s)` — the same 30, to the number. **A
    correct gate, correct output, stale input**, which is indistinguishable
    from a real failure by construction. Nothing needed committing in another
    owner's repository; the line was already there.
    The seeded session sent to add the missing lines found them already
    there and did something better instead: it corrected that line's
    **reason**, which the rename had copied from the old name's line rather
    than re-derived — the allowlist is kept green by what the tree NAMES, not
    by what `precedent.json` declares (its own preamble says so). Landed as
    that set's PR #85.
    The diagnosis is now mechanical too: the gate names its blocklist's own
    clone and how far behind it is whenever it fails
    ([PR #232](https://github.com/alex137/BestPractice/pull/232)), and the
    story is the second instance on the sibling-clone gotcha in
    [AGENTS.md](../AGENTS.md).

    **What is still open, and was this item's real finding.**
    [rename-updates-links](../practices/rename-updates-links.md)'s reasoning
    applies to an allowlist entry exactly as it does to a link — renaming a
    private repository means repointing every reference to it, and the
    repo-reference allowlist in a private blocklist is a reference. **Nothing
    checks it.** The rename on 2026-09-11 did carry its entry, by a session
    remembering to, which is the condition this repository normally refuses
    to rely on ([checkable-gets-checked](../practices/checkable-gets-checked.md)).
    A check is awkward but not impossible: the blocklist lives outside this
    repository, so it cannot be a `precedent_check.py` check here — the
    natural home is the private source's own checks, or
    [tools/very_deep_check.py](../tools/very_deep_check.py)'s
    repository-visibility pass, which already reads that file and already
    asks GitHub about each name.
    **Blocked on / out of scope:** a session that can write to the private
    individual source, and a decision about which of those two homes it
    belongs in. **Disposition:** wait (2026-09-11, Morgan — a session did not
    set this to `ask`; he is the one it waits on)

    **The other half of the same rename is closed** (2026-09-11): *whether a
    declared source repository has been renamed at all* is now asked by
    [tools/precedent_source_names.py](../tools/precedent_source_names.py), at
    [vendor-update-runbook](../practices/vendor-update-runbook.md)'s step 8. That
    does not close this item — an allowlist entry and a declared name are
    different references, and only the second is checked — but the two are
    now one rename apart rather than both invisible.

    **An earlier version of this item carried a handoff link** to a session
    seeded with the wrong diagnosis — go add three allowlist lines that
    already existed. That session was archived unused on 2026-09-11 rather
    than left to do it. The link is removed rather than kept, because a
    pasteable handoff to the wrong work is worse than none
    ([handoff-is-pasteable](../practices/handoff-is-pasteable.md) is about
    making the right handoff easy, not about having one).

## How It Closes

Not open until: a session that can write to the private individual source, and a decision about which of those two homes it belongs in.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
