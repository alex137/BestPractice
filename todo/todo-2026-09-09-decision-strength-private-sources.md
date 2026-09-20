---
slug:              todo-2026-09-09-decision-strength-private-sources
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "read-only access to `precedent-individual` and `precedent-team-repo-maintenance`, neither of which this session could attach (`add_repo` refused with *\"cross-tier adds are not supported in v1\"*) (`cross-source-rollout`)."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-09
closed:            null
---
## What

- <a id="decision-strength-private-sources"></a>**Carry `decision-strength` into the two private practice sets.** The
   `strength:` frontmatter key, the `Weak yes` phrase and the
   `decision-strength` check landed universal on 2026-09-09
   ([decisions/2026-09-09-decision-strength.md](../decisions/2026-09-09-decision-strength.md)).
   Two things the private sets need that this repo cannot do for them:
   **their own practice files carry `approved_by:` with no strength**, and
   nothing there is backfilled either (that is the rule, not an oversight) —
   but every practice landed in them *from now on* should carry the mark, so
   whoever has them attached should confirm their vendored
   [tools/precedent_check.py](../tools/precedent_check.py) is current enough to
   register the check, since a stale vendored engine simply will not run it
   and will report nothing. **And the individual set is where a standing
   personal rule about how approvals are recorded would live** — check
   whether one already contradicts this, particularly anything that treats a
   recorded approval as final by default.
   **Blocked-on:** read-only access to `precedent-individual` and
   `precedent-team-repo-maintenance`, neither of which this session could attach
   (`add_repo` refused with *"cross-tier adds are not supported in v1"*)
   (`cross-source-rollout`).

## How It Closes

Not open until: read-only access to `precedent-individual` and `precedent-team-repo-maintenance`, neither of which this session could attach (`add_repo` refused with *"cross-tier adds are not supported in v1"*) (`cross-source-rollout`).

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
