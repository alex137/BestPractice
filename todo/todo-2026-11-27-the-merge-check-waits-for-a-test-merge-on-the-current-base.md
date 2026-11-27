---
slug:              todo-2026-11-27-the-merge-check-waits-for-a-test-merge-on-the-current-base
kind:              analysis
domain:            engine
severity:          low
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-11-27
closed:            null
---
## What

- [ ] **Make the merge check wait when GitHub's test merge was built on an older base.** [tools/precedent_merge_check.py](../tools/precedent_merge_check.py) waits when the test merge's second parent is not the pull request's head. It does not wait when the first parent is no longer the base branch's tip, so for a while after the base takes a commit it judges a merge that no longer describes what would land (needs: a session working on the merge check; out of scope for the record cleanup that found it).

The trap and its workaround are in [the gotcha](../gotchas/gotcha-2026-11-27-the-merge-check-judges-a-test-merge-built-before-the-base-moved.md).

## How It Closes

`status` becomes `done` when a pull request whose base moved after its test merge was built is judged on a merge with the new base, or its refusal says the merge it read is stale, and a test holds that.
