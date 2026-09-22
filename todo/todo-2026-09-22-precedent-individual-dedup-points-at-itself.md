---
slug:              todo-2026-09-22-precedent-individual-dedup-points-at-itself
kind:              analysis
domain:            null
severity:          null
status:            done
disposition:       parked
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-22
closed:            2026-09-22
---
## What

- <a id="precedent-individual-dedup-points-at-itself"></a>**FALSE ALARM,
    closed same day. precedent-individual's
    `practices/deliverables-carry-no-process.md` carries `status: deduplicated`
    with `in_force_at: deliverables-carry-no-process`, and
    `tools/verify_harness.py --as-ci` reported that slug as unresolvable:
    "that slug does not resolve IN FORCE against the declared sources."**
    Filed as a likely pre-existing data bug on that report alone, without
    checking the actual target first -- wrong call, corrected the same
    session on Morgan asking "please fix."

    **The reference is correct.** precedent-individual's own
    `precedent.json` declares `precedent-shared-writing` as a sibling
    source at `../precedent-shared-writing`, and that repo's
    `practices/deliverables-carry-no-process.md` carries `status: active`
    -- exactly the slug `in_force_at` names, live and in force. Cloned
    `themorgan/precedent-shared-writing` (public, read-only) to check
    directly, symlinked it into the sibling path `verify_harness.py`'s
    pipeline expects, and re-ran the specific failing case
    (`precedent_sync_views.py --repo ../precedent-individual`): the
    "IN FORCE NOWHERE" finding does not reproduce once the source is
    actually present.

    **The real cause is this session's own directory, not the data.**
    `/home/user` held only two of precedent-individual's four declared
    sibling sources (`BestPractice`, `precedent-individual` -- missing
    `precedent-shared-repo-maintenance`, `precedent-shared-working-style`
    and `precedent-shared-writing`), which is exactly why the session-start
    notes this same session saw earlier said "shared/precedent-shared-writing
    did NOT resolve this session." A cross-source consumer check run
    against an incomplete sibling layout reports exactly this shape of
    false positive -- unresolvable, not wrong.

## How It Closes

(closed as a false alarm; no repository change needed)

## Notes

2026-09-22: filed from an unverified `verify_harness.py --as-ci` finding;
closed the same day after tracing it to this session's own incomplete
sibling-clone layout rather than the data. Lesson for next time: verify
a cross-source finding against the actual target before filing it as a
data bug, the same discipline `verify-postcondition` already asks for
anywhere else.
