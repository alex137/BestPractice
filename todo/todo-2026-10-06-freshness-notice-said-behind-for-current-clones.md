---
slug:              todo-2026-10-06-freshness-notice-said-behind-for-current-clones
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the next time a session-start notice calls a clone BEHIND that is current minutes later, with that session's start-up output kept"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-06
closed:            null
---
## What

A consumer session (2026-10-05/06) reported that its
session-start notice called three set clones BEHIND their origin main, at
58c0c1e, e9067e3 and 8a1476d. Minutes later, before the session had run
anything that moves a clone, they were at 9bc7e28, 2c01664 and 1023855,
which was current. Its hypothesis was that the freshness check runs before
the hook that fast-forwards the clones.

**Checked 2026-10-06, and that is not the order.** In this repository's
[.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh), and in
[tools/bootstrap.sh](../tools/bootstrap.sh) that the consumer hook template
delegates to, `precedent_refresh_sources.py --apply` runs before
`precedent_engine_freshness.py --quiet`. No other session-start or
per-prompt hook in the consumer template moves a set clone. What moved them
is not established. Two candidates, neither measured:

- The refresh skipped them: off their branch, or with changes of their own,
  and printing that only to its own output, which the hook sends to
  `/dev/null` on errors.
- Something outside the hooks updated them after the notice: the cloud
  harness bringing attached repositories current at the same time as the
  start-up hooks run.

**Done the same day, whatever the cause:** the freshness report reads a
live clone again just before calling it BEHIND, so a clone that moved
during the run is judged on what it holds now. The planted case is in
`check_freshness_covers_every_declared_source`, and fails without the
re-read.

## How It Closes

The cause is measured the next time it happens, with that session's
start-up output kept, and fixed where it lives, or the symptom does not
come back across a few weeks of session starts.
