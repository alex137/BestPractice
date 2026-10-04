---
slug:              todo-2026-10-03-consumer-rehearsal-before-the-ladder-produce
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "A separate session-load budget for the sets a person brings, set in their individual set, rather than charging them to a repository's ceiling or trimming the ladder"
decision_strength: assented
waiting_on:        "Morgan: land claude/staging-optional-user-display-i4tewn into staging, then the set rollout order below"
noted:             2026-10-03
closed:            null
---
## What

- <a id="consumer-rehearsal-before-the-ladder-produce"></a>**A rehearsal
  on four consumer repositories found staging not ready to Produce.**

  A separate session gave each of four consumers (kind `consumer`) a
  scratch clone of its own main with the real sibling sets beside it, and
  ran three states: its current engine; staging's engine alone; and a full
  Update Vendors against a BestPractice whose main was staging. The
  practice-set rehearsal ([spec/LADDER_OPT_IN_PLAN.md](../spec/LADDER_OPT_IN_PLAN.md))
  could not have caught these: a practice set renders with `build_views`,
  and a consumer with [tools/precedent_sync_views.py](../tools/precedent_sync_views.py).

  1. **A rule that requires the ladder drops out of every consumer.** The
     sync leaves out the sets a person brings before it resolves, and the
     resolver counts `provides` only over the sources it is handed. An
     individual set's two `requires: ["ladder"]` rules therefore vanish,
     and a deduplicated individual rule pointing at a ladder rule reads as
     in force nowhere.
  2. **After Produce, Update Vendors fails in every consumer.** The sync's
     removal guard knows a withdrawal only from a retired file still at its
     source, and `precedent_move.py --withdraw-from-universal` deletes the
     file. Its record, [record/WITHDRAWN_FROM_UNIVERSAL.md](../record/WITHDRAWN_FROM_UNIVERSAL.md),
     is not read by the guard and does not reach a consumer. Sixteen rules
     read as lost, and the guard's own remedy (`--allow-removals`) would
     also drop the rules in point 1.
  3. **The session-load ceiling.** With the ladder brought,
     `.precedent/SESSION_PRACTICES.md` is about 650 tokens, over two of the
     four consumers' ceilings, so every push there is refused. Decided:
     the sets a person brings get a budget of their own, set in their
     individual set (Morgan, 2026-10-03, strength: assented).
  4. Smaller:
     - `precedent_update.py --from-ref` took the engine from the ref and
       the catalogue from main;
     - `precedent_push_check.py --tier` with an unknown name silently ran
       the full check;
     - a consumer's follow-up notes said its branch had deleted rules it
       never touched.

  Each consumer's own follow-ups after its Update Vendors (links to moved
  practices, a new check's findings) belong to the plan's step 13 and are
  not listed here.

## Closes when

Points 1 to 4 are fixed in BestPractice with harness cases shown failing
without each fix, and a rerun of the consumer rehearsal, Update Vendors
included, passes in every consumer it reaches.

## Notes

- <a id="rerun-2026-10-03"></a>**The rerun (2026-10-03, against staging
  `2f1e5895`, then this branch).** Same four consumers, scratch clones of
  each main with real sibling sets beside them, three states plus a full
  Update Vendors against a BestPractice whose main is staging, and again
  with `--from-ref`.
  - **Points 1 to 4 are gone.** `ladder-required` and `promote-only` are
    in AGENTS.md, practices/ and MANIFEST.json in all four; no removal
    refusal and no `--allow-removals`; the session file is within budget
    with the sets at their staging; no follow-up notes; `--from-ref` takes
    the catalogue from the ref when run from a clone checked out at that
    ref. Its opening line still says `main @ <the ref's commit>`.
  - **Nine more failures only a consumer shows, all fixed on
    `claude/staging-optional-user-display-i4tewn`,** each with a harness
    case shown failing without it: a view already generated got no list
    (`6077a9ca`, `81489d13`); a stale view named the wrong cause
    (`a66e1b0f`); Update Vendors left its repoint of
    `process/upstream/tools/` unstaged, so the commit it asks for kept a
    session-start step silently doing nothing (`a746d690`); a root
    GLOSSARY.md was created where a repository keeps its glossary in
    docs/, the commit backstop rebuilt views before the person's fixer
    stamped their source, and `MAP.source.md` was outward-facing to the
    headline check (`99273a89`, `90c95eaf`); links to a removed practice
    in AGENTS.md's own text and in non-Markdown files went unlisted, and
    vendored engine files were listed as the repository's
    (`90c95eaf`, `776a88eb`, `fe8e0783`).
  - **With that branch, every consumer passes on what the release owns.**
    One passes its bare push check on the committed update. Two fail only
    on their own AGENTS.md link to `go-update`, which Update Vendors now
    names as left for the repo; the fourth only on its own hook's link to
    `file-mention-links`, from an earlier shared-set rename and not this
    release. Those are step 13's.
- <a id="rollout-order"></a>**Rollout order the rerun measured.** With the
  sets at their main, the session file is 650 tokens against two
  consumers' ceilings of 500 and 300: the brought-set
  budget lives on precedent-individual's staging, so its main must carry it
  before Produce. Consumers get the commit backstop from the individual
  set's `bootstrap/commit-identity.sh`, which has neither the rebuild nor
  the new fixer order until that set takes Update Vendors after Produce;
  until then a commit does not rebuild MAP.md, and the push check's
  views_sync catches it.
- <a id="calls-for-morgan"></a>**Calls for Morgan, not made here.**
  One consumer's hand-written GLOSSARY.md (a rule its own AGENTS.md says
  lives there) was overwritten on 2026-09-15 with its map;
  the instruction to regenerate rather than restore named the map only, and
  the migration has no glossary restore. Another consumer does not
  declare `precedent-shared-writing`, so sixteen rules that moved there
  read as in force nowhere; staging's engine says so, the current one hid it.
- Stays open: the rerun passes on the branch, not on staging as it stands.
  Closes when the branch is on staging and a short rerun there agrees.

