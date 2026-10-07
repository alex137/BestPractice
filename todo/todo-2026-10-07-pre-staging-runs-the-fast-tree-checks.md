---
slug:              todo-2026-10-07-pre-staging-runs-the-fast-tree-checks
kind:              manual
domain:            practice
severity:          null
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Approved in a narrower form: at Booked, a tree check's finding outside the change is kept when this push caused it -- it was not there before the push, judged by today's rules -- not every tree finding"
decision_strength: decided
waiting_on:        null
noted:             2026-10-07
closed:            2026-10-07
---
## What

**Proposal: a push to `pre-staging` also runs the tree checks that take seconds and need no network.** Today a pre-staging push gets the basic tier only (markdown lint, leak gate, commit-author checks), per the tier rule in [tools/precedent_branches.py](../tools/precedent_branches.py) (Morgan, 2026-09-25, strength: decided: "the default for everyone should be all branches other than the above never get tested beyond the basic markdown test when pushed to"). So a failure the full check would catch surfaces at the next Promote, for whoever runs it, often in work that is not theirs.

On 2026-10-07 a Promote failed `claude-only-surface-has-a-parallel`: the permanent-pointer hook change had added `.claude/hooks/precedent-hooks.sh` to pre-staging without a row in [templates/harness/PARALLELS.md](../templates/harness/PARALLELS.md). The session promoting for an unrelated fix wrote the row on its fix branch. That check reads two files and finishes in well under a second; it would have refused the original push.

What it would cost: the `tree`-scope checks of [tools/precedent_check.py](../tools/precedent_check.py) that touch no network add seconds to a pre-staging push, against fifteen minutes and an unrelated session's attention at Promote time. The harness and the deep check stay where they are.

Raised by Alex (S. Alexander Jacobson) on 2026-10-07, after the Promote above. It changes a rule Morgan decided, so it waits on Morgan.

## How It Closes

Morgan decides. If yes: [precedent_branches.py](../tools/precedent_branches.py) gives the basic tier the fast tree checks, with a harness case that a pre-staging push missing a PARALLELS row is refused. If no: the reason is recorded here and the item is closed.

## Decision (2026-10-07)

**Approved, in a narrower form than proposed.** Morgan, 2026-10-07: *"Okay, approved. Let's do it ... We can do it your way, but note in the todo and the PR etc the version you're doing, and why"* (strength: decided).

**What is built.** A push into `pre-staging` already ran every practice check, tree checks included, across the whole repository (`precedent_check.py --full-sweep --changed-files-only`); what it discarded was any finding naming a file outside the change. Now a **tree** check's finding outside the change is kept when **this push caused it**: the same checks run once more, with this commit's rules (`tools/`, `practices/`, `precedent.json`) laid over the tree the push started from, and a finding that is not there is the push's. A finding that was already there stays a note, now named by check and file. A finding about a commit is left to the push check's own history step. The work is `_caused_by_this_push` in [tools/precedent_check.py](../tools/precedent_check.py), and the harness case in `check_changed_files_only_judges_the_change` replays today's miss: a new hook with no PARALLELS row is refused at Booked, and the next, unrelated push is not.

**What is not built, and why.** The proposal as written, keeping every finding of the fast tree checks, would have caught the PARALLELS row. It would also have kept the repository's standing debt, and refused an unrelated push over it. That is the failure fixed earlier the same day: in a private consuming repository a one-file note was refused four times, over files it never touched, after a sync brought in a rule the repository did not meet yet. Which file a finding names is the wrong test either way; whether the push caused it is the right one, and the push check already asks it of a working-branch push (`already_landed` in [tools/precedent_push_check.py](../tools/precedent_push_check.py)). "Fast" and "no network" also stop mattering: nothing new runs unless a tree check set something aside, and then only those checks, once.

**Cost.** Nothing when no tree finding lands outside the change. Otherwise one temporary worktree and one run per check that set something aside, typically a few seconds.

