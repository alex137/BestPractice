---
slug:              todo-2026-10-07-pre-staging-runs-the-fast-tree-checks
kind:              manual
domain:            practice
severity:          null
status:            open
disposition:       null
remind_on:         null
blocked_on:        "a decision by Morgan, who set the branch tiers (2026-09-25, strength: decided)"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-07
closed:            null
---
## What

**Proposal: a push to `pre-staging` also runs the tree checks that take seconds and need no network.** Today a pre-staging push gets the basic tier only (markdown lint, leak gate, commit-author checks), per the tier rule in [tools/precedent_branches.py](../tools/precedent_branches.py) (Morgan, 2026-09-25, strength: decided: "the default for everyone should be all branches other than the above never get tested beyond the basic markdown test when pushed to"). So a failure the full check would catch surfaces at the next Promote, for whoever runs it, often in work that is not theirs.

On 2026-10-07 a Promote failed `claude-only-surface-has-a-parallel`: the permanent-pointer hook change had added `.claude/hooks/precedent-hooks.sh` to pre-staging without a row in [templates/harness/PARALLELS.md](../templates/harness/PARALLELS.md). The session promoting for an unrelated fix wrote the row on its fix branch. That check reads two files and finishes in well under a second; it would have refused the original push.

What it would cost: the `tree`-scope checks of [tools/precedent_check.py](../tools/precedent_check.py) that touch no network add seconds to a pre-staging push, against fifteen minutes and an unrelated session's attention at Promote time. The harness and the deep check stay where they are.

Raised by Alex (S. Alexander Jacobson) on 2026-10-07, after the Promote above. It changes a rule Morgan decided, so it waits on Morgan.

## How It Closes

Morgan decides. If yes: [precedent_branches.py](../tools/precedent_branches.py) gives the basic tier the fast tree checks, with a harness case that a pre-staging push missing a PARALLELS row is refused. If no: the reason is recorded here and the item is closed.
