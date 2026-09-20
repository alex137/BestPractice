---
slug:              todo-2026-09-08-level-repo-naming
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
noted:             2026-09-08
closed:            null
---
## What

- <a id="level-repo-naming"></a>**Evaluate renaming the practice-set repositories so the level is
  visible in the name.** Morgan, 2026-09-08: *"I keep on being hesitant in
  my mind about the level filenames ... What if the structure is:
  `precedent.level-individual.me` and
  `precedent.level-team.team-name-here`."* His argument is that the current
  names do not say what they are, and that a naming scheme carrying the
  level would make the whole vocabulary system legible at a glance.

  **Not done that day, deliberately, and this is a real trade rather than a
  refusal:**

  - The clarity argument is correct. `precedent-team-tms` does not tell a
    reader that `tms` is a team name, and `precedent-individual` does not
    say whose.
  - Against it: [source-naming](../practices/source-naming.md) fixes these
    names *by convention*, with [spec/SOURCE_NAMING.md](../spec/SOURCE_NAMING.md)
    and a check behind it — so this changes the rule, not just the names.
  - The names are referenced from **outside** the repositories: per-machine
    user-level config paths, `precedent.json` `path` entries, sibling-clone
    assumptions like `../precedent-team-repo-maintenance`, the `add_repo` calls
    three separate `AGENTS.md` banners instruct, and every gotcha entry that
    names one. A rename is a real sweep, and the per-container paths break
    **silently**.
  - `.me` reads as a domain suffix, and a dot in a repository name collides
    visually with a file extension in exactly the tooling that already
    splits on dots.

  **What was done instead**, as the cheaper half of the same goal: `level`,
  `source` and `level repo` are now defined in [GLOSSARY.md](../GLOSSARY.md)'s
  engine-vocabulary section, which was the actual gap — the words were used
  hundreds of times and defined nowhere.

  **Disposition:** wait

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
