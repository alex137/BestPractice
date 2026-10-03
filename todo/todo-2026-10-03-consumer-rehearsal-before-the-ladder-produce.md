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
waiting_on:        null
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
