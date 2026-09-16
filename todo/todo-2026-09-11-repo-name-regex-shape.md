---
slug:              todo-2026-09-11-repo-name-regex-shape
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
noted:             2026-09-11
closed:            null
---
## What

- <a id="repo-name-regex-shape"></a>**Think about the shape of the leak
   gate's repository-name rule: it refuses `owner/name` and ignores `name`.**
   Raised by Morgan, 2026-09-11, in the same breath as deciding the team
   sets' names are not private
   ([decisions/2026-09-11-team-set-names-are-not-private.md](../decisions/2026-09-11-team-set-names-are-not-private.md)).
   That decision settles those two names and settles nothing about the
   mechanism, which is what this item is for.

   **The asymmetry.** The private-owner allowlist matches only the
   owner-qualified form. Whether the gate covers a mention therefore depends
   on a formatting choice the writer never knew they were making: *"see
   `themorgan/precedent-team-writing`"* is refused, *"clone
   `precedent-team-writing` beside your repo"* sails through. Both sentences
   disclose the same thing to a reader who knows the account.

   **Why the obvious fix is not available**, and this is the constraint any
   answer has to respect: a bare-name pattern cannot simply be added.
   Measured 2026-09-11 against `precedent-beta-v01` — `precedent-team-writing`
   appears 25 times and `precedent-team-working-style` 13, in
   [precedent.json](../precedent.json), [practices/source-naming.md](../practices/source-naming.md),
   [spec/SOURCE_NAMING.md](../spec/SOURCE_NAMING.md), this file and the
   document-project templates. A shared repository has to declare its team
   sources by name. The rule cannot treat that as a leak.

   **Shapes worth weighing, none of them chosen:** make the refusal depend on
   whether the OWNER appears anywhere nearby rather than adjacent to the name;
   scope a bare-name rule to prose and exempt declaration files by kind;
   distinguish a name that only exists as a repository from one that is also a
   declared source path; or accept the asymmetry deliberately and say so in
   the template, so the next person reads a decision instead of a gap. The
   last one is cheap and may be right.

   **blocked-on:** nothing mechanical — the gate lives in
   [tools/leak_gate.py](../tools/leak_gate.py) here, and the measurement above is
   already done. It is queued for thought rather than permission, which is
   what Morgan asked for.

   **Disposition:** wait ([open-item-disposition](../practices/open-item-disposition.md)).

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
