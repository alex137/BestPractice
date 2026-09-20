---
slug:              todo-2026-09-06-multiple-team-sources-disagree
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing but a decision about what shape the answer takes. Parked deliberately at Morgan's request, 2026-09-07 — do not design it in passing."
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-09-06
closed:            null
---
## What

- <a id="multiple-team-sources-disagree"></a>**Define what happens when a consumer repo imports multiple `team`
   sources that disagree.** See PRACTICE_ENGINE_PLAN.md's `## Deferred`
   section (added 2026-09-03, alongside that session's precedence reorder)
   for the detail — not duplicated here. **Half-closed 2026-09-06**: the
   *silent* case is gone. Two team-level sources claiming one slug used to
   resolve to whichever `precedent.json` listed second, reported only as an
   ordinary `overridden:` notice on stderr — indistinguishable from a
   legitimate higher-level override, and decided by config file order.
   [tools/precedent_resolve.py](../tools/precedent_resolve.py) now fails
   loudly there, which is what PRACTICE_ENGINE_PLAN.md said it did all
   along ("the resolver fails loudly if two same-level practices claim one
   slug"). Two team sources that do NOT collide still resolve together,
   with a harness case each way. What is still open is the *design*
   question the plan defers: whether a consumer should be able to express a
   preference between two teams at all, rather than being told to rename
   one. Revisit when a real multi-team-import case appears — a second team
   set now exists (`precedent-team-tms`, 2026-09-05), so that is closer
   than it was.

   **The real case appeared 2026-09-07, twice in one day, and was resolved
   by removing the collision rather than answering the question.** Two
   sessions independently landed `fail-gracefully` and `bold-key-phrases`
   into *both* team sets, each doing the obviously right thing. Confirmed by
   running it: `precedent_resolve` raised `ResolveError` — *"nothing orders
   two sources at the same level, so there is no answer to which one wins"* —
   so any repository declaring both team sources could not resolve at all.
   Nothing was broken in practice, because no repository declared both.
   Morgan's decision was to promote both to universal and delete them from
   the team sets, which is right when the rule is genuinely shared: two
   teams wanting the identical rule is what a universal rule looks like.

   **That does not answer this item, and the two must not be confused.**
   Promotion works only while the teams want the *same* rule. The open
   question is the same slug meaning *different* things to two teams, and
   every remedy available today is a workaround for it:

   - **Rename one** — cheap, and wrong as a habit: the slug is the identity
     a session searches by, so two names for one concept is the folklore
     problem relocated.
   - **Retire one** — only honest when one team was wrong.
   - **Move one to another level** — there is no level below team except
     repo-local, which does not reach a team's other repositories.
   - **Promote** — requires the rule to be genuinely shared, as here.

   So a rule two teams both want, differently, still has no home. Options
   worth weighing: an explicit tie-break a *consuming* repo declares (it
   knows which team it belongs to, which neither source does);
   source-qualified slugs at the point of use; or accepting the refusal and
   requiring that no repository declare two team sources.

   **Blocked on:** nothing but a decision about what shape the answer takes.
   Parked deliberately at Morgan's request, 2026-09-07 — do not design it in
   passing.

## How It Closes

Not open until: nothing but a decision about what shape the answer takes. Parked deliberately at Morgan's request, 2026-09-07 — do not design it in passing.

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
