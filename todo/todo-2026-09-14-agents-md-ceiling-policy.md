---
slug:              todo-2026-09-14-agents-md-ceiling-policy
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       parked
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"I think we should do B, C, and D. now\" -- Morgan picked raising the ceiling on purpose (to a number with a stated reason), splitting the quick index, and capping the generated occasion index, from a costed menu of five options."
decision_strength: decided
waiting_on:        null
noted:             2026-09-14
closed:            2026-09-14
---
## What

- <a id="agents-md-ceiling-policy"></a>**Decide the STANDING answer to
    `AGENTS.md`'s ceiling: a reduction pass every time somebody hits it, or a
    higher declared number.** Item
    [1](todo-2026-09-14-agents-md-over-its-ceiling.md) closed the instance and item
    [82](todo-2026-09-13-session-load-under-20k.md) is done and parked, so the policy
    question has had no home anywhere.

    **The instance is closed and the pressure is not.** Measured on
    `precedent-beta-v01` at `74eb776`, 2026-09-14: `AGENTS.md` is **11,553
    tokens against the 12,000** in
    [tools/session_load_budgets.json](../tools/session_load_budgets.json), so
    there are 447 tokens of headroom. The only reason there are any is that
    the file went over three separate times in two days and somebody paid a
    reduction pass each time — the gotchas preamble (12,026 → 11,917,
    [PR #357](https://github.com/alex137/BestPractice/pull/357)), then the
    quick index, where 14 rows had grown from *"looking for X → go to Y"* into
    abstracts of the documents they only need to point at (11,917 → 11,546 at
    `5b2f1ab`; item 1 records 11,538, measured on that branch before the merge
    that carried it). Both cuts were duplication rather than content, and both
    were paid mid-task by sessions doing something else.

    **What makes it structural rather than a run of bad luck:** every gotcha,
    every quick-index row and every standing command comes out of the same
    12,000, the occasion index is GENERATED and cannot be hand-trimmed, and
    the catalogue grows by design.
    [session-load-budget](../practices/session-load-budget.md) forbids the easy
    move — raising the number to clear a red — and names the alternative,
    which is what the two passes above did. Nobody has costed what doing that
    forever is worth against the alternatives.

    **A session is on it, rooted here and seeded with the whole question**,
    created 2026-09-14:
    [session_016g7xNkvTFffAchb3vDtBxp](https://claude.ai/code/session_016g7xNkvTFffAchb3vDtBxp).
    Morgan asked for a separate tab in his own words — *"this is bigger so it
    deserves a separate tab"* — so the spawn is his, not the session's.
    **Strength:** decided (2026-09-14, Morgan), on the tab; the question's
    answer is what that session is for and is not decided by anyone yet.

    **COSTED FOR MORGAN 2026-09-14**, re-measured at `50d82ff` after the
    seed's own figures went stale within hours — `AGENTS.md` **11,590 of
    12,000, 410 tokens (3.4%)**, down from 447 at `74eb776` with nobody
    trimming or adding prose in between. Reproduce any figure below with
    `python3 tools/session_load_trend.py`.

    **The one measurement that reorders the options: what consumes the
    headroom is GENERATED.** The occasion index is **3,383 tokens, 29.2% of
    the file, 106 entries**, and it has grown every single day — 1,136 on
    2026-08-31, 2,462 on 09-09, 2,753 on 09-11, 3,053 on 09-12, 3,211 on
    09-13, 3,377 on 09-14. That is **≈160 tokens a day over the fortnight and
    ≈232 over the last three days**. With the resident block it is **4,340
    tokens (37%) that no reduction pass may touch**. At those rates the
    current headroom is gone in **under two days**, whether or not anybody
    writes a word.

    **Section costs, for any option that proposes cutting something:**
    preamble 2,112 (18.2%) · resident block 967 (8.3%, generated) · occasion
    index 3,383 (29.2%, generated) · standing instruction 322 · quick index
    2,671 (23.0%) · gotchas index 1,532 (13.2%) · working-in-this-repo 429 ·
    conventions 171.

    **A. A standing reduction pass on a stated trigger.** Formalises what
    already happens: at a declared headroom floor, the next session to touch
    the file pays a pass before pushing. *Cost:* it keeps the tax and keeps
    landing it on whoever is unlucky — **four crossings in two days, three
    sessions, none of which added the thing that broke it** — and it fires
    roughly weekly forever at the measured growth. The cheap material is also
    spent: item 82's pass found that outside the gotchas *"nothing else in the
    file was a duplicate"*, the gotchas are already split to
    [record/GOTCHAS.md](../record/GOTCHAS.md), the command stories are gone, and
    the quick index is already back to pointers. **The next pass cuts live
    content**, which is a different decision from the four before it.

    **B. Raise the ceiling deliberately, with the reason recorded.**
    Permitted — [session-load-budget](../practices/session-load-budget.md)
    forbids raising one *to clear a red check*, not raising one on purpose.
    *Cost, and it is the finding that surprised this session:* **a raise buys
    days, not months.** To 13,000 ≈ 6–9 days; to 14,000 ≈ 10–15; to 16,000 ≈
    19–28; to 20,000 — which alone equals the whole-session target — ≈ 36–53.
    The generated growth eats any number. **A raise defers this question; it
    does not answer it.**

    **C. A second split, in item 82's shape.** The only block big enough to be
    worth moving is the **quick index, 2,671 tokens**, to a pointer at
    [MAP.md](../MAP.md). *Cost:* it exists precisely to stop sessions searching
    the repo, so moving it re-adds the hop it was built to remove, and it was
    *just* compressed on 2026-09-14 — cutting it again is cutting muscle. Buys
    ≈11–17 days at the measured rates, then the same question returns.

    **D. Cap the generated occasion index, the way the resident block is
    capped.** [tools/build_views.py](../tools/build_views.py) already refuses to
    write an over-budget resident block; the occasion index has **no cap at
    all**. A cap moves the cost onto the session ADDING a practice, at the
    moment it adds one, and makes the decision about the thing that actually
    grew. *Cost, measured rather than assumed:* of 113 active practices, **33
    are reachable ONLY by the occasion index** — `applies_to: ["**"]`, which
    matches everything and therefore routes nothing, and no `gates:` entry.
    For those, dropping an index line **un-routes the rule**. The other ≈73
    carry a specific path glob or a gate; **whether that channel fires at the
    right moment is a per-practice reading this measurement does not
    establish.** It also makes adding a practice harder in a project whose
    thesis is capturing practices.

    **E. Move something else out of the always-loaded set.** *Cost:* there is
    no candidate. [CLAUDE.md](../CLAUDE.md) is 55 tokens and
    `.precedent/SESSION_PRACTICES.md` (3,081) is the private sources' only
    channel into a session. **Named because leaving an option out is a
    decision taken on somebody's behalf, not because it is live.**

    **RECOMMENDED: D and B together, in that order — and the pair is the
    recommendation, because neither works alone.** D is the only option that
    stops the growth rather than absorbing it; B is the only one that stops
    the next honest sentence from triggering a pass at 3.4% headroom. A and C
    are both "absorb it again", and the material they absorb it with has
    nearly run out. **What has to happen first for D to be safe:** the 33
    index-only practices need a real `applies_to` glob or a gate, or the cap's
    first bite silently un-routes a rule — that is work, and it is the reason
    D is not simply done here.

    **Not done, deliberately:** no ceiling was raised. The seed forbade it and
    [session-load-budget](../practices/session-load-budget.md) puts the
    equivalent resident-block choice on the person in the same words.

    **BUILT HERE**, because every option above needs it and none of them is
    chosen: [tools/session_load_trend.py](../tools/session_load_trend.py) reports
    headroom, the hand-written/generated split and the growth rate per
    surface, and its `headroom_notice()` is called from
    [tools/precedent_gate.py](../tools/precedent_gate.py) at the **merge and push
    gates** — so a session is told the DISTANCE to the ceiling instead of
    meeting it as a red check. The threshold is `headroom_floor_pct` in
    [tools/session_load_budgets.json](../tools/session_load_budgets.json); it is
    a **notice, never a failure**, on the ground that a gate blocking on an
    *approaching* ceiling would manufacture exactly the raise-it pressure the
    practice exists to resist. It fires today at 3.4%.

    **Record the answer with
    [decision-strength](../practices/decision-strength.md)** — `decided` only if
    Morgan can be quoted choosing an option, `assented` for a bare "ok" to the
    recommendation above.

    **CLOSED 2026-09-14 — Morgan picked B, C and D**, from the menu above:
    *"I think we should do B, C, and D. now"*. **Strength:** decided — he
    chose rows rather than approving a proposal, and the recommendation he
    was answering was D+B, so C is his own addition.

    **C, the split.** The quick index had grown to **88 rows, 2,671 tokens**.
    The full table moved to [WHERE_THINGS_ARE.md](../WHERE_THINGS_ARE.md) and the
    twelve rows sessions reach for constantly stayed inline, with a pointer
    row. **No row was dropped** and nothing was rewritten. The trap worth
    recording: [quick-index](../practices/quick-index.md) is a *resident*
    practice and is mechanically checked for **at least five rows in the
    instructions file**, so moving the whole table would have broken a live
    check and the practice's own intent — the short-table split satisfies
    both. **11,590 → 9,336.**

    **D, the cap.** `occasion_index_tokens` in
    [tools/session_load_budgets.json](../tools/session_load_budgets.json), set at
    **3,600** against 3,377 measured, enforced by
    [tools/build_views.py](../tools/build_views.py)'s
    `OccasionIndexBudgetExceeded` — **the first budget the generated half has
    ever had.** Deliberately tight: the cap is meant to be met often, because
    meeting it is the decision it exists to force. Its message names the fix
    *and* the trap — never drop an `occasion:` from a practice whose
    `applies_to` is `["**"]` with no gate, since the index is then its only
    channel. Adding `reduction-pass` below took the index to 3,421, so **179
    tokens remain**, which is the cap working as intended.

    **B did not come out as expected, and the ceiling is UNCHANGED at
    12,000.** C reclaimed 2,254 tokens and took headroom from 3.4% to 22.2%,
    so there was no pressure left for a raise to relieve. What B asked for was
    a number chosen on purpose rather than a ratchet artifact, and that is
    what it now is: **12,000 = 5,600 generated cap** (resident 2,000 +
    occasion 3,600, the most the generated half can ever be) **+ 6,400
    declared prose allowance**, against 4,996 of prose today. **The guarantee
    that buys:** if the generated half filled both caps the file would reach
    10,596, so **generated growth alone can no longer push it over**. Every
    future crossing is prose somebody chose to write — visible, attributable
    and trimmable, which the four crossings on 09-13/14 were not. Raising it
    above 12,000 stays Morgan's call and nothing here needs it; this was
    flagged to him in the reply rather than decided quietly.

    **The menu is documented and has a command.** Morgan asked for both in the
    same message — *"And document these options, it's a good list for reducing
    it in the future. Do we have a command to do a 'reduction' pass listing
    what you did?"* — so the five options became the six-step menu in
    [practices/reduction-pass.md](../practices/reduction-pass.md), a **universal**
    practice defining the standing command **"Reduction pass"**.
    [session-load-budget](../practices/session-load-budget.md) points at it
    rather than carrying a second copy.
    `python3 tools/session_load_trend.py --since <ref>` computes the
    before/after ledger the report needs, excluding any surface that has no
    `before` rather than booking it as growth.

    **What is NOT claimed:** that the short quick index is as good as the full
    one was. A session that needs a long-tail row now follows one link where
    it used to read the row inline, and nothing measures what that costs —
    the same honest gap [82](todo-2026-09-13-session-load-under-20k.md) recorded for the
    gotchas split. **Disposition:** parked (2026-09-14, closed as done)

## How It Closes

Already closed 2026-09-14 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
