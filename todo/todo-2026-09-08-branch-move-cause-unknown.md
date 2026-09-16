---
slug:              todo-2026-09-08-branch-move-cause-unknown
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

- <a id="branch-move-cause-unknown"></a>**Something moved this checkout off its working branch
  mid-session on 2026-09-08, and the cause was not found.** The reflog
  recorded a checkout onto `precedent-beta-v01` and a fast-forward pull,
  three minutes after a commit, with nothing asking for either.
  `precedent_vendor_engine.py seed`, `precedent_refresh_sources.py --apply`
  and `checkin.py fresh` were each replayed against a throwaway clone on a
  feature branch and **none of them moved `HEAD`**, so the three obvious
  suspects are ruled out and whatever does it is outside this repo's own
  tools. [tools/precedent_session_check.py](../tools/precedent_session_check.py) now detects the drift; nothing
  prevents it. Full account in [AGENTS.md](../AGENTS.md)'s gotchas.

  **Disposition:** wait

  Detection is in place and the loss is recoverable from the reflog, so
  this costs a session minutes rather than work. Worth another look only if
  it recurs — and if it does, capture `ps` and the reflog timestamp before
  doing anything else, because the missing evidence is the whole problem.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
