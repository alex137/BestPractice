---
slug:              todo-2026-09-14-phase3-snapshot-is-not-a-snapshot
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "one call: whether these anchors should be a frozen record read from a pinned commit, or be retired as anchors and kept as prose with an \"as of phase 3\" date. Until it is made, editing an original-52 practice trips a gate that is right to fire and wrong about who is at fault. **The trap is narrower t"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="phase3-snapshot-is-not-a-snapshot"></a>**The phase-3 "point-in-time
    record" is not one: it freezes WHICH practices count and reads what they
    say TODAY, so editing any of the original 52 moves a figure two documents
    recite.** Measured 2026-09-14, and the measurement is the demonstration:
    adding a `## Detail` to [two-check-levels](../practices/two-check-levels.md)
    — one of the original 52 — moved
    [catalogue_stats.py](../tools/catalogue_stats.py)'s
    `phase3_snapshot_stats()['with_detail']` from 21 to 22, and
    `scripts-assert-properties` failed on the anchor reciting 21 in
    [spec/PRACTICE_FORMAT.md](../spec/PRACTICE_FORMAT.md)'s "The Rule/Detail
    Split".
    **The half-fix is visible in the function's own docstring.** It records
    that computing these over the growing `practices/` directory "would fail
    every anchor the first time anything was added after phase 3 -- which is
    exactly what happened", and the remedy taken was to filter the population
    by `source_practice_number` 1..52. That freezes the set, not the text: the
    section content still comes from `_load()`, which reads the working tree.
    So the figure is stable against *additions* and moves on any *edit* to an
    original practice.
    **Neither document knows that.** `spec/PRACTICE_FORMAT.md` says in its own
    parenthetical that both figures are scoped to the original 52 "so they stay
    a stable record of what phase 3 delivered rather than drifting", and
    [spec/PRACTICE_ENGINE_PLAN.md](../spec/PRACTICE_ENGINE_PLAN.md) restates the
    same figure.
    **Do not refit the anchor** — [scripts-assert-properties](../practices/scripts-assert-properties.md)
    forbids exactly that, and here refitting would paper over the bug rather
    than record it. A real snapshot reads the phase-3 text, which upstream can
    do from its own history and a pinned ref; the population filter then
    becomes redundant.
    **Blocked-on** one call: whether these anchors should be a frozen record
    read from a pinned commit, or be retired as anchors and kept as prose with
    an "as of phase 3" date. Until it is made, editing an original-52 practice
    trips a gate that is right to fire and wrong about who is at fault.
    **The trap is narrower than "do not edit an original-52 practice", and the
    exact boundary was measured 2026-09-14 by enumerating `ANCHORS`.** Of the
    four, one reads the LIVE catalogue and three read the frozen snapshot,
    which returns exactly two figures: `with_detail` moves when a `## Detail`
    is added or removed, `long_rules` when a Rule crosses 150 words. A `Why`,
    a `Story`, an `Install`, or any practice outside 1..52 moves neither. Note
    that `long_rules` is recited in TWO documents -- `spec/PRACTICE_FORMAT.md`
    and `spec/PRACTICE_ENGINE_PLAN.md` -- so a Rule crossing 150 words trips
    two anchors at once, and a session that fixes only the document named in
    the first failure will be back.
    **Two mechanisms are in play here with OPPOSITE remedies, and conflating
    them is the likelier mistake.** An `ANCHORS` figure is prose in a document
    of record: never refit it, because making it agree with the present
    destroys the thing it recorded. A `doc_sync` generated block --
    `spec/LOADER.md`'s catalogue table -- is a render target reading the live
    catalogue, and the correct action there is always
    `python3 tools/doc_sync.py --write`. Editing one practice can trip both in
    the same run, which is how it presented when this was found: `LOADER.md`
    drifted 76 -> 77 on "Carrying a `## Detail`" and wanted regenerating,
    while the anchor reciting 21 wanted leaving alone.
    **Pending behind it:** a clause for
    [two-check-levels](../practices/two-check-levels.md) saying a check is
    reported by what it found (`0 failed` / `0 violated`) and never by its
    passed count — which is a property of the tree, so quoting it across a
    repository boundary invites a comparison that means nothing. Written and
    verified 2026-09-14, then reverted unlanded because it is an edit to an
    original-52 practice and trips the anchor above. It came from a real case:
    a consuming repo reported "52 passed, 0 violated" against upstream's "44
    passed, 0 violated" for the same change.

## How It Closes

Not open until: one call: whether these anchors should be a frozen record read from a pinned commit, or be retired as anchors and kept as prose with an "as of phase 3" date. Until it is made, editing an original-52 practice trips a gate that is right to fire and wrong about who is at fault. **The trap is narrower t

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
