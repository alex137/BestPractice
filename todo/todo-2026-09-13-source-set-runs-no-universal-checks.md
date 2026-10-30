---
slug:              todo-2026-09-13-source-set-runs-no-universal-checks
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
waiting_on:        "Produce (step 5 of 5) in BestPractice, so Update Vendors can take the 2026-10-30 engine change from main into the three sets"
noted:             2026-09-13
closed:            null
---
## What

- <a id="source-set-runs-no-universal-checks"></a>**A practice set now READS
    the universal rules and still RUNS none of universal's mechanical
    checks.** Shape 3 landed 2026-09-13
    ([spec/SOURCE_SET_PROSE_GAP.md](../spec/SOURCE_SET_PROSE_GAP.md)): a session
    rooted in an individual or team set resolves the universal source and
    reads its 94 occasion entries out of an untracked
    `.precedent/SESSION_PRACTICES.md`. **That is the reading half only.** The
    checks those practices declare in `checked_by:` are not materialized into
    the set, so a universal rule that is mechanically enforced everywhere else
    is advisory there — the set can violate it and its own gate stays green.

    **Morgan asked for this to be noted as an issue to review, 2026-09-13**,
    off the sentence that closed the shape-3 explanation: *"a session in a
    source set would read universal's rules but still not run universal's
    mechanical checks there."*

    **It is a known, deliberate boundary rather than an oversight**, and the
    reason is on the record in
    [tools/precedent_session_practices.py](../tools/precedent_session_practices.py)'s
    own header, written for the consumer case and true verbatim here: turning
    the other sources' checks on before a repo's `not_binding` exemptions are
    written *"would make the gate red for reasons nobody has judged yet"*.
    The same audit found six source-supplied checks reporting things the
    consuming repo could not act on because the practice was about a
    different KIND of repository — and a practice SET is the most different
    kind there is, so the count there is likely higher, not lower.

    **What review means concretely**, in order: run the universal catalogue's
    checks against one set and count how many are (a) real findings, (b) not
    applicable to a set at all, (c) already covered by that set's own
    re-declared copy. Only (a) is worth wiring; (b) is what `not_binding` is
    for; (c) is the redeclaration `binds_publishers` was supposed to end, so
    any survivor there is its own finding. `binds_publishers` (#261,
    2026-09-12) already teaches a check to bind the repo that publishes the
    practice, which is the nearest existing machinery and the place to start
    reading.

    **DECIDED 2026-09-14: run the measurement, wire nothing.** Morgan took the
    recommendation as written — *"okay let's implement your suggestion"* —
    with no argument for it, so **strength: assented (2026-09-14, Morgan)**.
    Wiring before the count is what the `not_binding` reasoning above warns
    against, and the cost of guessing wrong is a permanently red gate in four
    repositories.

    **MEASURED 2026-09-14, and the measurement half CLOSES on its stated
    condition.** The set was `precedent-team-writing`, copied to scratch and
    given the current upstream engine — every file in
    [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
    `ENGINE_FILES`, 20 of them — so the run says what a REFRESHED set does,
    not what a 249-commit-stale one does. Nothing was wired, and nothing was
    written to any set.

    **As the gate stands today, 3 universal checks reach a set and 42 do not
    — and the 42 skip for ONE reason, not 42.** Every one prints *"no
    practices/<slug>.md in this repo, so the practice is not in force here"*.
    That is a file-presence test, and shape 3 deliberately does not satisfy it:
    it routes the universal text through an untracked
    `.precedent/SESSION_PRACTICES.md` rather than committing a second copy.
    The three that do reach it are exactly the three carrying
    `binds_publishers` — `catalogue-carries-stories`, `practice-links-travel`,
    `generated-artifact-provenance`. So that machinery is not just the place to
    start reading; it is already the whole of the answer, in production.

    **With the presence gate forced open in the scratch copy, the whole
    catalogue against one set is 24 passed, 5 violated, 1 advisory, 23
    skipped.** Sorted the way this item asked:

    - **(a) real findings: one, and it is a defect in a CHECK, not in the
      set.** `code-cites-practice` reads
      `tools/precedent_close_detect.py`'s citations of `declared-pronouns` and
      `fail-gracefully` as typos, because it resolves a slug against the local
      `practices/` directory — which in a practice set holds that set's own
      catalogue and nothing else. Both slugs are real upstream. Every set given
      the current engine would go red here, on engine files it did not write.
    - **(b) not applicable to a set at all: the other four.** Three are
      expectations of a consuming repo's `AGENTS.md` that a 17-practice
      catalogue does not meet by design — `quick-index`,
      `environment-gotchas`, `two-check-levels` — and `routing-audit` names
      `tools/routing_audit.py`, which is not in `ENGINE_FILES` at all. This is
      what `not_binding` is for.
    - **(c) already covered by the set's own re-declared copy: none.** The
      set's 17 practices meet the registry at three slugs — `draft-marker`,
      `no-stale-counts`, `deliverables-carry-no-process` — and not one of them
      is a universal practice. They are the writing team's own, with checks in
      the shared engine, which is that engine working as designed. The
      redeclaration `binds_publishers` was meant to end is genuinely absent.

    **Half the catalogue cannot run in a set at any gate setting**, which this
    item did not know: 13 of the 23 skips are a tool that is not vendored —
    `doc_lint.py`, `doc_sync.py`, `doc_lifecycle.py`, `title_case.py`,
    `practice_audit.py`, `model_audit.py`. Opening the gate buys nothing for
    those without a second, larger decision about what a set contains. The
    other 10 skip because there is honestly nothing there to check.

    **What the count says about wiring, now that it is counted rather than
    reasoned:** opening the presence gate today would turn four repositories
    red for five reasons, four of which nobody would act on, and would not
    enforce one universal rule that is not already enforced. The
    `binds_publishers` three are the rules whose SUBJECT is a published
    catalogue — a check reaches a set when the set is what the rule is about,
    not because the set can read the rule. That is the boundary, and the
    measurement endorses it.

    **What is left, and it is small:** teach `code-cites-practice` to resolve a
    slug across the resolved sources rather than the local directory. Not done
    in the same breath as the measurement, on purpose —
    [tools/precedent_check.py](../tools/precedent_check.py)'s own header warns
    against "a behaviour change nobody asked for, in every consuming repo at
    once", and changing how a slug resolves is exactly that. It wants its own
    branch and its own harness case.
    **It pairs with item 87**, found 2026-09-14: a set cannot even run
    `precedent_show.py` on a universal slug, because `practices/` there holds
    the set's own files only. That is the same boundary from the READING side
    — the rules arrive as one-line clauses and nothing else — so whoever takes
    the measurement should read both items together rather than discover the
    second one halfway through.

    **The reason this was queued is spent.** It was queued as "a measurement
    pass with an unknown answer, not a change with a known shape" — the answer
    is above, and the shape that is left is one check's slug resolution.
    **Disposition:** wait (2026-09-14) — the 2026-09-13 `ask` was Morgan asking
    for this to be reviewed, and he has reviewed it; the `code-cites-practice`
    fix is ordinary work that needs nothing from him.

    **BUILT 2026-10-30, on Morgan's "Act. Let's build this."** He had
    noticed BestPractice's way of working not applying in sessions rooted
    in the three practice sets (2026-10-29: a session opened on
    `precedent-individual`, `precedent-shared-ladder` and
    `precedent-shared-writing` only). Re-measured first: the ladder set
    ran 56 checks and skipped 67, 44 of them "not in force here". The
    change in [tools/precedent_check.py](../tools/precedent_check.py):

    - **A set's gate reads the sources it declares.** `_practice_file`
      also looks in the `practices/` of each source the set's own
      precedent.json declares (`_declared_source_practice_dirs`): for
      every set, universal at `../BestPractice`. The person's individual
      set and the sets they bring are not read, so a set's gate does not
      differ by who runs it. Where the source is not on disk (a set's own
      CI) the gate skips as before.
    - **`code-cites-practice` resolves across those sources**, the item's
      one leftover from 2026-09-14: `timestamps-carry-offset` no longer
      reads as a typo in the writing set, and a set's deduplicated stub
      (`curly-quotes`) yields to universal's active copy.
    - **`skips_in_sets`**, a reason on a check whose subject a set does not
      keep by design, reported as SKIPPED with that reason: `quick-index`,
      `environment-gotchas` and `two-check-levels` (hand-kept sections of
      a project's AGENTS.md; a set's is the generated loader block) and
      `routing-audit` (its tool ships to consumers only). The 2026-09-14
      (b) verdict, now in the engine rather than in three sets'
      `not_binding`.
    - **`layered-practice-packs` sees a set's session channel**: it read
      only `session-start.sh`, so with the gate open every universal
      practice in a set read as reachable by nothing. It now reads what
      settings.json starts, and treats what the tracked block defers as
      carried by `.precedent/SESSION_PRACTICES.md`.

    **What it finds, measured against scratch copies of all three sets**
    (engine patched, nothing written to any set): the real findings left
    are `document-status-header` in all three (spec files with no
    lifecycle frontmatter, or a status and `closed:` date that disagree)
    and `deep-check` in the ladder set (three `tools/checks/` scripts and
    no `tools/checks/tests/run_all.sh`), plus the individual set's
    `set-words-stay-in-their-set`, red before this change too. Pinned by
    `check_a_set_runs_the_checks_its_declared_sources_put_in_force` in
    [tools/verify_harness.py](../tools/verify_harness.py), which fails
    with the change reverted.

    **Morgan's question, answered on the record:** the reply rules a set's
    session sees at the end of a turn were never copies; they are read
    live from `../BestPractice` already. What did not reach a set was the
    mechanical checks, which is what this changes.

    **Landed and fixed, 2026-10-30, on Morgan's "Fix the problems you
    found ... and act and booked on the above".** The engine change is on
    staging ([#1416](https://github.com/alex137/BestPractice/pull/1416)),
    with two follow-ups found by running it:
    [#1417](https://github.com/alex137/BestPractice/pull/1417)
    (`deep-check` read the ladder set's six tests of its own tools as
    stale) and a source level read past the one reader. Each set's
    findings are fixed on its staging: the ladder set's `run_all.sh` and
    plan header ([precedent-shared-ladder#146](https://github.com/themorgan/precedent-shared-ladder/pull/146)),
    the writing set's header, the individual set's seven. The individual
    set's `set-words-stay-in-their-set` was a measuring artifact (scratch
    copies resolved their siblings elsewhere): in the real clone it skips,
    as designed. What is left is the engine reaching the sets: Update
    Vendors takes it from BestPractice's main.

## How It Closes

Done when a session rooted in each practice set, with universal on disk
beside it, runs universal's checks there -- the engine change on the
landing branch, Update Vendors run in all three sets -- and each set's
full check is green, its findings above fixed rather than exempted.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
2026-10-30: built on a feature branch; closes on the condition above.
