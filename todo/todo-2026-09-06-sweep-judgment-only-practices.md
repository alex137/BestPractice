---
slug:              todo-2026-09-06-sweep-judgment-only-practices
kind:              analysis
domain:            content
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
closed:            2026-09-07
---
## What

- <a id="sweep-judgment-only-practices"></a>~~**Sweep the team and individual sets' judgment-only practices.**~~
    [tools/full_practice_audit.py](../tools/full_practice_audit.py) reports 49
    judgment-only practices across the three sources. The 2026-09-06
    pre-launch audit judged the universal slice's highest-yield ones and
    fixed what they found. **Partially swept 2026-09-06** (second pass, see
    [spec/PRELAUNCH_AUDIT.md](../spec/PRELAUNCH_AUDIT.md)'s "The judgment-only
    sweep, partially done"): `fail-gracefully` produced seven real fixes and
    `durable-list-anchors` one; `branch-links`, `rule-links`,
    `blank-blocklist`, `install`, `quiet-checks` and
    `registry-source-of-truth` came back clean. **Round two, same day**
    (see that document's "The judgment-only sweep, round two"): nineteen of
    fifty-one now judged; `automation-issues` and
    `match-parsed-id-not-prefix` were both violated and are fixed, and eight
    more came back clean or not-applicable with the reason recorded.
    **Roughly thirty-two remain** — mostly moment-of-work practices with no
    standing repo state to sweep, and editorial ones that need a reader
    rather than a script. **Round three, same day: the sweep is COMPLETE** —
    all 51 judged (see that document's "The judgment-only sweep, round
    three"). Four more violations fixed (`lead-with-what-it-is`,
    `bold-key-phrases`, `volatile-rules-carry-dates`, and
    `resolved-issue-note-updates`, that last one violated by the sweeping
    session itself), and the remaining 28 came back clean or not-applicable
    with the reason recorded so no later session re-derives them. The sweep
    also turned up a defect no practice pointed at: `tools/title_case.py`
    was corrupting inline code spans in committed headings.

    **Done — closed 2026-09-07.** This item contradicted itself: it declared
    the sweep COMPLETE ("all 51 judged") and then carried *"blocked on
    nothing but session budget — take them one at a time"*, so it read as
    both finished and not started depending on which sentence you stopped
    at. The second half is now measured rather than argued. Across **all 39**
    practices carrying `checked_by: null` in the two private sets: none has
    an empty `## Install`, the shortest is 177 characters, the median 393,
    and **not one** uses the "too hard to check" shape
    [checkable-gets-checked](../practices/checkable-gets-checked.md) forbids.
    Every one records a considered, specific no, which is what that practice
    asks for — an attempt and a recorded reason, not a check at any cost.

    One case read as unreasoned to a keyword scan and is the opposite:
    `catalogue-carries-stories` **is** checked mechanically, by the universal
    catalogue's own `precedent_check.py`, and its `checked_by` is `null`
    precisely so that set does not carry a second implementation of one rule.
    39 of 39 accounted for. **A `checked_by: null` count is not a defect
    count** — the same correction `precedent-team-tms`'s 0 of 2 needed.
    Full context: [spec/PRELAUNCH_AUDIT.md](../spec/PRELAUNCH_AUDIT.md) and
    [spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md).

## How It Closes

Already closed 2026-09-07 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
