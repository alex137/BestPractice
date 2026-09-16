---
slug:              todo-2026-09-14-applies-to-sprawl
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
noted:             2026-09-14
closed:            null
---
## What

- <a id="applies-to-sprawl"></a>**The path-trigger channel prints a wall of
    rules for markdown and almost nothing for code, and a consuming repo
    declined it over exactly that.** Measured on 2026-09-14 in a consuming repository — a private documents
    repo with one markdown deliverable — and re-measured here against `precedent-beta-v01` at
    [74eb776](https://github.com/alex137/BestPractice/commit/74eb776277105b70fa504470de1dc3c521b0fd33)
    before writing this item; the figures move with the catalogue, so
    re-measure again before acting on it.

    **What the channel costs, per tool call.**
    [tools/precedent_paths.py](../tools/precedent_paths.py) — wired in a
    consuming repo as `.claude/hooks/precedent-paths.sh` — fires on
    PreToolUse for every `Edit` and `Write`, not once per session. Run
    against real files in that repo, resolving all four sources (universal,
    three team, repo-local, individual):

    | File | Rules | Chars | Tokens | Time |
    |---|---|---|---|---|
    | `content/PERSONAL_TODOS.md` (its one deliverable) | 28 | 19,643 | ≈4,910 | 0.07s |
    | `TODO.md` | 22 | 15,781 | ≈3,945 | 0.06s |
    | `tools/light_check.py` | 5 | 4,831 | ≈1,207 | 0.06s |
    | `.github/workflows/light-check.yml` | 3 | 2,430 | ≈607 | 0.06s |

    Universal-only, in this repository, the same shape: `TODO.md` 15 rules /
    ≈3,168 tokens, `README.md` 12 / ≈2,805,
    [tools/precedent_paths.py](../tools/precedent_paths.py) 5 / ≈1,207, a
    workflow file 2 / ≈458. Latency is nothing. Three consecutive edits to a
    markdown deliverable is ≈15,000 tokens of largely the same rules, and a
    wall of 28 rules before each edit is skimmed rather than read — which is
    the failure `reply-is-short` names one layer up, arriving through the
    mechanism built to prevent it. The consequence is not only spend:
    that repo **declined `precedent-paths.sh` on 2026-09-14** over this, so
    the channel is costing a repo that wants it.

    **The framing this item arrived with is half wrong, and correcting it
    kills the cheap fix.** The measurement that raised it counted
    `applies_to: ["**"]` as the cause: 69 of 113 active practices here (62
    on-demand, 7 resident), 117 of 179 with all four of that repo's sources
    resolved. Both counts reproduce exactly. But **`"**"` already means "not
    path-routed"** — [tools/precedent_paths.py](../tools/precedent_paths.py)
    drops it (`narrow_globs = [g for g in globs if g != '**']`, there since
    phase 2, 2026-08-31, so every vendored copy has it), and
    [tools/routing_scope.json](../tools/routing_scope.json)'s own `_note` says
    so in as many words. **Not one of those 69 is printed by the channel.**
    So the semantics change that would have been the cheap fix is already
    the semantics, and the `"**"` share is not the number to watch.

    **What actually drives it is markdown fan-in.** Of 103 active on-demand
    practices here, 11 are routed `**/*.md` — plus what is file-specific
    (`TODO.md`, `AGENTS.md`, `PRACTICES.md`) — and each source adds its own.
    Code and configuration land at 2 to 5 rules because their globs genuinely
    select; markdown is where the channel collapses, and markdown is what a
    document repository edits all day.

    **What this item asks for, then:**
    - **Tighten `**/*.md`.** A practice governing outward-facing prose
      ([readers-vocabulary](../practices/readers-vocabulary.md),
      [headline-capitalization](../practices/headline-capitalization.md)) is not
      the same routing as one governing any document at all
      ([doc-references-are-links](../practices/doc-references-are-links.md)).
      The distinguishing-condition rule
      [tools/routing_scope.json](../tools/routing_scope.json)'s `_note` already
      settled on is the test to apply; every glob that survives unchanged
      carries its justification there, as the `"**"` entries already do.
    - **Decide whether the channel caps what it prints** — N most severe, or
      a summary line plus slugs to expand — so the cost stops scaling with
      the catalogue. This trades completeness for being read. **This session's
      position: cap it.** An uncapped wall is already not read at 28 rules,
      so "complete" is nominal, and a summary line with slugs keeps the
      expansion one command away. A cap is also the only one of these
      remedies that bounds a *consuming* repo's cost, which is the cost that
      lost the adoption.
    - **A mechanical check** in [tools/precedent_check.py](../tools/precedent_check.py)
      that fails, or warns, when what the channel prints for a representative
      path crosses a declared ceiling. The shape already exists:
      [session-load-budget](../practices/session-load-budget.md) declares a
      ceiling per always-loaded surface in
      [tools/session_load_budgets.json](../tools/session_load_budgets.json) and
      ratchets down. The threshold to declare is the *printed* size for a
      markdown path, not the `"**"` share — per the correction above, that
      share would measure nothing.

    **Is this a gap in the routing audit? No — it is the opposite direction,
    and they should stay separate.**
    [routing-audit](../practices/routing-audit.md) asks *did every practice that
    should have fired, fire?* — under-firing, a practice with a wrong or
    missing trigger that nobody notices. This asks what over-firing costs the
    reader and the context window. Its `coverage` pass walks the same globs
    and would report every one of these 28 as correctly matched, because they
    are. Folding a cost ceiling into an audit built for misses would give one
    mechanism two opposed success conditions. Same input file
    ([tools/routing_scope.json](../tools/routing_scope.json)), different
    question.

    **Blocked on / why this is queued rather than done:** the first bullet is
    a judgement pass over 11-plus globs whose effect is felt in every
    consuming repo, and the second and third need a number somebody decides.
    Re-routing a practice changes when it reaches a session — the failure
    mode [routing-audit](../practices/routing-audit.md) exists for — so it is
    not a tidying edit one session makes on its own.

    **Disposition:** wait ([open-item-disposition](../practices/open-item-disposition.md)).

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
