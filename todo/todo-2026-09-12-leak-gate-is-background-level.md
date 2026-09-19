---
slug:              todo-2026-09-12-leak-gate-is-background-level
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          ""Yes, make this one universal." -- Morgan chose universal over individual level for leak-gate-is-background."
decision_strength: decided
waiting_on:        null
noted:             2026-09-12
closed:            2026-09-13
---
## What

- <a id="leak-gate-is-background-level"></a>~~**Decide whether
    `leak-gate-is-background` belongs at team or universal level rather than
    individual.**~~ **Answered 2026-09-13, by him: universal** — *"Yes, make
    this one universal."* Asked to choose between the two readings below, he
    took the one that says the rule is about what the gate prints rather than
    about what he personally wants to be interrupted by, so `strength: decided`
    ([decision-strength](../practices/decision-strength.md)).

    **Step 1 of the move is done**: the practice is landed at universal as
    [practices/leak-gate-is-background.md](../practices/leak-gate-is-background.md),
    rewritten person-neutral (no first person, no link into a private set) with
    the per-person half kept out of the Rule — a universal rule must not force
    the quiet directive on anyone, which is the constraint this item itself
    identified. **Step 2, deduplicating the individual copy, landed the same
    day**, as
    [TODO.md's `leak-gate-is-background-dedup` item](todo-2026-09-13-leak-gate-is-background-dedup.md)
    records; [spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md)'s land-first
    ordering meant the interim state was a deliberate duplicate, never a
    gap.

    Original reasoning, kept because it is what the decision was made against.
    It landed 2026-09-12 in the individual set — a session never
    relays a leak-gate note, never proposes a blocklist term, and never asks
    whether to add one; the recommendations arrive in
    [very-deep-check](../practices/very-deep-check.md)'s repository-visibility
    pass instead. Morgan, the same day, asking for this item: *"I should
    consider later (not now) if the new rule to not repeatedly ask me about
    blocklist ideas ... should be on a team or universal level as opposed to
    personal? I don't know but I don't want to decide now because I want to
    finalize this set of changes."*

    The test is [layered-practice-packs](../practices/layered-practice-packs.md)'s
    — *would this hold in an unrelated repo?* Two readings, and they disagree.
    The nuisance it ends is not personal: any repository with a private
    blocklist prints the same note on every run, and any session will relay
    it, so the rule reads universal. Against that, what a person wants to be
    interrupted about is exactly the kind of thing an individual set exists
    for, and somebody who wants those notes is not wrong to want them. The
    mechanism is already level-neutral — `stem-notes off` and
    `auto-cover-bare-names on` are per-person directives in each blocklist,
    so a universal rule would not force either switch on anyone; it would only
    say what a session does with what the gate prints.
    Moving it is [spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md)'s
    procedure, not a rewrite.

    **Since 2026-09-12 there is a second test to apply here**, and the two
    readings above are exactly what it was written for:
    [rule-level-by-reach](../practices/rule-level-by-reach.md) asks *would this
    still be true for a different person?* before asking about an unrelated
    repository. It does not settle this item -- that is still his call, and
    the disposition below stands -- but it says which question to put to him:
    whether the rule is about what the gate prints (reach: anyone) or about
    what he wants to be interrupted by (reach: him).
    **No disposition line, because the item is no longer open** — it carried
    `ask` from 2026-09-12, blocked on his decision while he finished the change
    itself, and that decision is the answer above.

    He had asked to be reminded in about three days, and a Routine was set to
    fire on 2026-09-15 and open a session on this item. **It was deleted on
    2026-09-13, once the decision made it pointless**, and the Routine list came
    back empty afterwards.

    **A session first wrote here that nothing in this repository could cancel
    it.** That was wrong, and wrong in the way
    [verify-decomposition](../practices/verify-decomposition.md) already forbids —
    *never encode an impossibility as an assertion until you have varied the
    inputs that would relieve it*. A Routine is not repository state, which is
    true and was the whole of the reasoning; what went unchecked is that the
    session had tools addressing the scheduler directly, and one call listed the
    Routine. **The rule existed and covered it**, so nothing new was written
    ([mistakes-become-rules](../practices/mistakes-become-rules.md)'s
    proportionality guard). Recorded here because the shape recurs: a limit on
    what a *repository* can reach, stated as a limit on what the session can do.

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
