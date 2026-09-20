---
slug:              todo-2026-09-12-register-is-a-live-field-in-one-identity-json-and-absent-fro
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-12
closed:            2026-09-14
---
## What

- **`register` is a live field in one identity.json and absent from the
  skeleton every other one is built from.** Noticed 2026-09-12 while adding
  `pronouns` to
  [templates/practice-set-individual/identity.json.template](../templates/practice-set-individual/identity.json.template).
  `register` was added to the live individual set on 2026-09-10 and makes
  exactly the argument `pronouns` now makes — a fact about a person, which a
  shared repo cannot know — but it never reached the template, so a set
  bootstrapped today has no slot for it, and the team-level
  `default-register`'s non-technical fallback applies to its owner forever
  without anyone being asked. The fix
  is the same shape as this change: a `{{PERSON_REGISTER}}` placeholder, a
  `verify()` finding naming the absent key, and a line in the bootstrap
  procedure. It was left out here deliberately rather than missed — the
  approval covered pronouns.
  **DONE 2026-09-14**, as part of the contributor-access build: the skeleton
  carries `"register": "{{PERSON_REGISTER}}"` with its own comment,
  `precedent_bootstrap_source.py --verify` names an absent key, and
  [spec/BOOTSTRAP_NEW_SOURCES.md](../spec/BOOTSTRAP_NEW_SOURCES.md)'s step 5d
  asks for it beside pronouns. The one live set already has the field; no
  existing set was edited.
  **Disposition:** wait (done, kept for the record)

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
