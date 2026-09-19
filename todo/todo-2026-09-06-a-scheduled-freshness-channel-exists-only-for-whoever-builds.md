---
slug:              todo-2026-09-06-a-scheduled-freshness-channel-exists-only-for-whoever-builds
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          ""No weekly updates. I had that weeks ago, but we're not doing that anymore; this is now really complex and deserves hand attention and issues come up every time and I'm on it every day anyway." -- Morgan killed the weekly refresh channel outright."
decision_strength: decided
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-14
---
## What

- **A scheduled freshness channel exists only for whoever builds one.** The
  two channels shipped here — the bootstrap warning and
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py) —
  are both incidental: they fire when someone happens to be bootstrapping a
  set, or happens to be working in this repo. A set nobody touches for a
  month is told nothing for a month. The scheduled channel that would close
  that was added to both source templates on 2026-09-06 and **removed the
  same day, deliberately**: a cron job phoning a remote weekly, spending an
  adopter's Actions minutes and opening pull requests in their repository, is
  not something a universal template gets to decide on their behalf.
  [spec/BOOTSTRAP_NEW_SOURCES.md](../spec/BOOTSTRAP_NEW_SOURCES.md) records the
  shape in full so nobody re-derives it.

  **SUPERSEDED 2026-09-14 in its second half.** This item used to end "it is
  an individual-level preference now", which was true for eight days. Morgan
  killed the weekly refresh outright — *"No weekly updates. I had that weeks
  ago, but we're not doing that anymore; this is now really complex and
  deserves hand attention and issues come up every time and I'm on it every
  day anyway."* **Strength:** decided
  ([decision-strength](../practices/decision-strength.md)). So there is no
  individual-level copy to point at either, and the replacement channel is a
  person saying `Update Vendors`
  ([vendor-update-runbook](../practices/vendor-update-runbook.md)). **Blocked
  on:** nothing — this is no longer an open question. A set nobody touches
  for a month still goes a month unwarned, and that is now the accepted cost
  rather than a gap awaiting a cron.

## How It Closes

Already closed 2026-09-14 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
