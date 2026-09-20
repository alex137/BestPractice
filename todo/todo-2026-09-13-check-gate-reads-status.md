---
slug:              todo-2026-09-13-check-gate-reads-status
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"Document the disctinction please\" -- Morgan chose to document the file-presence-vs-status distinction rather than change the gate."
decision_strength: decided
waiting_on:        null
noted:             2026-09-13
closed:            2026-09-13
---
## What

- <a id="check-gate-reads-status"></a>~~**Decide whether
    [tools/precedent_check.py](../tools/precedent_check.py)'s practice-backed gate
    should test a practice's `status` rather than whether its file exists.**~~
    **Decided 2026-09-13: document the distinction, do not change the gate.**
    Morgan, asked to choose between changing the gate and writing the
    difference down, answered *"Document the disctinction please"* (his
    spelling), `strength: decided` — he chose it against a stated
    recommendation rather than assenting to a bare proposal. Relayed to this
    session by another session rather than typed here, so it is a claim about
    a person and checkable with him.

    **Where it is written**, both in the same change:
    [tools/precedent_check.py](../tools/precedent_check.py)'s module docstring,
    beside the existing SKIPPED and EXEMPT paragraphs, which is where a
    session hits the reasoning; and
    [spec/ENFORCEMENT.md](../spec/ENFORCEMENT.md)'s "A check can bind the repo
    that PUBLISHES a practice", whose opening sentence *is* the file-presence
    gate. `run()`'s condition is untouched.

    The original finding follows, unchanged.
    `run()` skips a
    practice-backed check when `_practice_file(slug)` returns nothing, and that
    function looks for the file and nothing more. So a check whose practice is
    `deduplicated` keeps running, and prints as its failure message the
    `## Rule` of a file that says on its own face it is not in force from here.

    **In the case that raised it that was tolerable, and arguably right** — the
    rule really is in force one level up, and the stub's Rule still states it
    truly, so the message misleads nobody. The measurements are in
    [TODO.md's `leak-gate-is-background-dedup` item](todo-2026-09-13-leak-gate-is-background-dedup.md)
    above. What makes it a question rather than a shrug is that `retired` and
    `superseded` files are kept too, never deleted ([MAP.md](../MAP.md)'s
    withdrawn-practice table is built from them), so a check keyed to one of
    those would run with
    the same confidence and no rule in force behind it at all. Against
    changing it: file existence is what `rule_of()` needs in order to print
    anything; the engine already has one shared `is_in_force()` predicate that
    a status test would have to agree with rather than duplicate; and every
    consuming repo's check run changes shape the day it lands.

    **A second, independent instance, 2026-09-13**, which is the first evidence
    that this can make a verification read backwards rather than merely print a
    confusing message. An individual set's `practice-links-travel` was passing
    before that set's engine refresh, and it looked like `binds_publishers`
    already working. It was not: the set carries
    `practices/practice-links-travel.md` at `status: deduplicated` (withdrawn
    2026-09-11), and the leftover file alone was switching the check on. Two
    team sets with no such file reported `1 skipped` for the same check on the
    same engine — the control that separates the two explanations.

    **What that costs is a verification technique, not just a message.** A
    session confirming that a practice has been withdrawn from a set cannot use
    "its check still runs" as evidence of anything, in either direction:
    deduplicating the local copy and watching the check stay green proves
    nothing, because file presence alone produces that result. The decisive
    test is removing the file outright, which is how the flag was confirmed to
    genuinely carry the rule. Worth writing into whatever this decision becomes:
    **"the check ran" does not imply "the practice is in force"**, and the two
    are currently documented as the same thing.

    **Blocked on / out of scope (resolved):** it was a decision about the
    engine's own behaviour rather than a defect, and the session that found it
    deliberately changed nothing. Morgan decided it on 2026-09-13. The item
    carries no disposition because it is no longer an open item.

## How It Closes

Already closed 2026-09-13 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
