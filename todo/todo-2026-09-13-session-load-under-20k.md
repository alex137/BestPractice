---
slug:              todo-2026-09-13-session-load-under-20k
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       parked
remind_on:         null
blocked_on:        null
batch:             null
decision:          ""bolded lead only" -- Morgan picked the gotchas-index-split option from a costed menu of five."
decision_strength: decided
waiting_on:        null
noted:             2026-09-13
closed:            2026-09-13
---
## What

- <a id="session-load-under-20k"></a>**Get what every session loads under
    20,000 tokens.** **DONE 2026-09-13 — 14,386.** Measured with
    [tools/build_views.py](../tools/build_views.py)'s own `_approx_tokens`:
    [AGENTS.md](../AGENTS.md) 11,468, `.precedent/SESSION_PRACTICES.md` 2,863,
    [CLAUDE.md](../CLAUDE.md) 55. It started the day at 22,904.

    **Two passes, and the second is the one that did it.** The first removed
    1,118 tokens of text that was already present in full somewhere a session
    reads anyway — the eight Precedent commands' coining stories, three
    convention bullets, and the doubled halves of the private-source block
    (#287). That left 21,786, still over, and nothing else in the file was a
    duplicate.

    **The rest was a judgment call and Morgan took it**, from a costed menu of
    five: *"bolded lead only"*, `strength: decided` — he picked a row rather
    than approving a proposal. The gotchas section became an **index**: one
    line per trap, the symptom and a link, with all 36 entries moved to
    [record/GOTCHAS.md](../record/GOTCHAS.md) **in full**. 8,858 tokens of section
    became 1,462 of index. **Verified word for word** — 6,778 words out of the
    section, 6,778 into the record, identical — because the whole argument for
    the split is that it changes the loading and not the text.

    **The story guarantee moved with the text rather than being dropped.**
    [environment-gotchas](../practices/environment-gotchas.md) now describes both
    shapes and says when to split;
    [tools/precedent_check.py](../tools/precedent_check.py) follows the links and
    applies the same "no bare fixes" test to the record, with five stated cases
    in [tools/verify_harness.py](../tools/verify_harness.py) including the
    discriminating one; and
    [tools/very_deep_check.py](../tools/very_deep_check.py)'s currency pass reads
    the record's bodies, so it still sees 36 entries and 9,473 tokens instead
    of going quietly blind on one-line symptoms. Without that last piece the
    split would have silently retired the only thing that tells a stale gotcha
    from a live one.

    **What is NOT claimed: that the index is as good as the section was.** A
    session that recognises a symptom loses nothing; a session that has not hit
    the trap yet now meets one line where it used to meet the story, and
    nothing measures what that costs. The ceiling is ratcheted to 12,000 in
    [tools/session_load_budgets.json](../tools/session_load_budgets.json), so
    growth back toward the old figure is a decision somebody takes on purpose.
    **Disposition:** parked (2026-09-13, closed as done)

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
