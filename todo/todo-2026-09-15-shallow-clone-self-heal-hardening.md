---
slug:              todo-2026-09-15-shallow-clone-self-heal-hardening
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"Yes, please build that. GO merge.\" -- Morgan approved hardening the shallow-clone self-heal."
decision_strength: decided
waiting_on:        null
noted:             2026-09-15
closed:            2026-09-15
---
## What

- <a id="shallow-clone-self-heal-hardening"></a>**Harden the shallow-clone
    self-heal so a failed attempt is loud, and so a merely-behind (not
    falsely-diverged) shallow checkout gets a second try.** Full incident and
    the platform research behind it:
    [record/GOTCHAS.md g37](../record/GOTCHAS.md#g37), third occurrence,
    2026-09-15. This is scoped narrower than "prevent
    shallow clones" — that part is closed: a brand-new session already
    self-heals correctly, and a resumed session that predates the fix can
    only be reached from inside itself, once, which is not something a
    committed file can do. What is left to build:
    1. `session-start.sh`'s unshallow attempt gets one `timeout 90` try and,
       on failure, only a `WARN` line nothing re-surfaces. Retry once more
       with a second bounded window, and on a second failure write a marker
       (e.g. `.git/PRECEDENT_SHALLOW_UNRESOLVED`) that a later hook pass can
       see and surface loudly, instead of a line in stdout nobody reads back.
    2. `freshness-guard.sh`'s `_deepen_if_shallow` only fires from the
       divergence branch (`ahead != "0"`). Make the guard check `is_shallow`
       unconditionally on its own first run each session too, independent of
       whether the counts look diverged — a second, independent path to the
       same repair, so a SessionStart failure isn't the only chance.
    3. Fold both into [record/GOTCHAS.md g37](../record/GOTCHAS.md#g37) once built, and check whether the
       four private practice sets' vendored copies need the same refresh
       `tools/precedent_refresh_sources.py` already does for other hook
       drift.
    **CLOSED 2026-09-15 — built and merged.** Morgan: *"Yes, please build
    that. GO merge."* (`strength: decided`). Built exactly the three items
    above: `.claude/hooks/session-start.sh`'s unshallow block now retries
    once more on failure and leaves `PRECEDENT_SHALLOW_UNRESOLVED` in the
    git dir when both attempts fail; `freshness-guard.sh` (identical in
    `.claude/hooks/` and `templates/harness/claude-code/hooks/`, kept in
    sync) now calls `_deepen_if_shallow` unconditionally, before either
    function trusts its ahead/behind counts, and surfaces a loud `WARN` at
    session-start when the marker is still there; `templates/bootstrap.sh`
    (the consumer-repo equivalent of the session-start block, not originally
    scoped but the same class of fix, named here rather than left as a
    silent gap) got the same retry-and-marker treatment. Verified against
    fixtures reproducing g37's exact shape (a shallow clone whose disjoint
    graft reads as `0 behind, 0 ahead` before deepening, so the OLD code
    path skipped the update entirely rather than merely misreporting it) —
    the fixed code deepens first and fast-forwards correctly; a genuinely
    diverged branch still blocks as before, confirmed as a regression
    check. Rolls out to dependent repos the next time each runs `Update
    Vendors`, per
    [vendor-update-runbook](../practices/vendor-update-runbook.md); the
    four private practice sets' vendored copies still need
    `tools/precedent_refresh_sources.py --apply` by hand, tracked
    separately at [g20](../record/GOTCHAS.md#g20) rather than duplicated here.

## How It Closes

Already closed 2026-09-15 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
