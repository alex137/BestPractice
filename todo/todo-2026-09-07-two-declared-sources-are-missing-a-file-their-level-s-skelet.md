---
slug:              todo-2026-09-07-two-declared-sources-are-missing-a-file-their-level-s-skelet
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing but the work — both repos are reachable and pushable from a session that has them attached."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            null
---
## What

- **Two declared sources are missing a file their level's skeleton ships.**
  Found 2026-09-07 by the [very deep check](../spec/VERY_DEEP_CHECK.md)'s
  source-shape pass, once that check stopped reporting two false positives
  alongside them. `themorgan/precedent-individual` has no
  `config.json.sample`; `themorgan/precedent-team-repo-maintenance` has no
  `leak-blocklist.txt`. Both were migrated into place rather than
  bootstrapped, so neither ever passed through
  [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py),
  which is the same cause the `verify()` docstring already records for the
  team set's blocklist — that entry is about this one, still open.
  The blocklist matters more than the sample: an absent one is a gap, while
  an empty one is a deliberate state (`blank-blocklist`), and until it
  exists the leak gate's vocabulary layer has nothing of that set's own to
  check against.
  **Both fixes already exist, unlanded.** Found 2026-09-07 while writing up
  the branch sweep: `claude/pre-launch-audit-fixes-7wumzx` carries
  "Add the `config.json.sample` this set never got, being migrated not
  bootstrapped" in the individual set and "Add the `leak-blocklist.txt` this
  set never got, being migrated rather than bootstrapped" in the team set,
  both dated 2026-09-06. This item and that branch are the same finding,
  rediscovered a day apart because nothing asked what was sitting unmerged.
  **Do not merge those branches to close this** — both sit on a vendored
  engine 41 commits behind their own `main`, so merging would revert the
  engine to land two files. Cherry-pick the two files (and, in the
  individual set, `practices/my-identity-is-not-private.md` with its check
  and test, which are also unlanded), then close the branch.
  **Blocked on:** nothing but the work — both repos are reachable and
  pushable from a session that has them attached.

## How It Closes

Not open until: nothing but the work — both repos are reachable and pushable from a session that has them attached.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
