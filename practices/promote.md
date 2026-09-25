---
slug:        promote
title:       "\"Promote\" moves pre-staging into staging, with the full push check on the whole batch"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message says \"Promote\" about the branch tiers, or asks to move pre-staging into staging"
gates:       ["merge"]
index_clause: "\"Promote\" -- pre-staging into staging, fully checked, by a merge commit"
checked_by:  null
defines:     ["Promote", "pre-staging"]
command:     {"Promote": "Move everything waiting on pre-staging into staging: the full check runs on the whole batch, and staging moves only if it passes."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-25"
approved_by: "Morgan, 2026-09-25 -- the three branch tiers are his own
  design (\"to prestaging only the most minimal test; to
  staging/precedent-beta-v01 all local tests; and then to main, you get
  all those local tests AND the most important GitHub test\", strength:
  decided), with promotion by a person rather than a schedule (\"I think
  that it should not be on a cron\", decided). The word itself was the
  session's recommendation, approved with the plan as a whole: \"Otherwise,
  this looks great, let's do it, go ahead, go update\"."
strength:    assented
---
## Rule
When a message says **"Promote"** about the branch tiers -- the whole
message, or a clause like "promote pre-staging" -- run, in the repository
the work is in:

    python3 tools/precedent_branches.py --promote

It does the whole step, and a session adds nothing to it:

1. **Brings pre-staging up to date with staging** when staging has moved on
   its own (somebody pushed there directly), by a merge. A conflict stops it
   before anything is pushed.
2. **Makes one merge commit of pre-staging onto staging** -- always a merge
   commit, never a fast-forward, so no pre-staging commit's `[skip ci]`
   line can become staging's head and silence the GitHub test on the pull
   request into main.
3. **Runs the full push check on exactly that commit**, in a throwaway
   worktree, and **pushes it to staging only if it passes.** A pass already
   recorded for the same tree is reused.

**Report what it printed, plainly**: the commits promoted, or -- on
`PROMOTE REFUSED` -- the failing check and the batch it was run on. A
refusal is fixed on pre-staging, like any other edit, and promoted again;
never by pushing the batch to staging some other way.

**It can take as long as the full check does** -- minutes in this
repository. Run it with a long timeout, or in the background, and keep
working; staging does not move until it is done, and nothing else waits on
it.

**Not practice promotion.** Moving a practice *candidate* into the
catalogue is also called promotion, and a message about a candidate or a
practice means that step, which has its own tool. This command is about
branches, and takes no argument.

## Why
Pre-staging exists so that many windows can save in seconds: a push there
gets only the basic check. That trade is only safe because every commit
still gets the full check before it reaches staging, and this is where it
gets it -- once per batch rather than once per window, which is the whole
saving. A promotion that could push without the check, or a check that
could pass one commit and push another, would turn the saving into a hole.
So the command checks the exact commit it pushes, and pushes by itself.

## Story
Morgan, 2026-09-25, in a brainstorm about why saving had gone from a second
to twenty minutes once the local checks came back: work from eight windows
at once into one branch with only the fastest check, and pay for the full
suite once, from a background window, when the batch moves on. He ruled out
a scheduled promotion in favour of a push a person starts. The plan, with
the decisions and how firmly each was made, is
[spec/BRANCH_TIERS_PLAN.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/BRANCH_TIERS_PLAN.md).

## Install
Nothing to install beyond the engine: [precedent_branches.py](../tools/precedent_branches.py) ships in
every kind's engine files. Its behaviour is pinned by [verify_harness.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/verify_harness.py)'s
`check_promote_pre_staging` -- a failing batch leaves staging where it was,
a passing one lands as a merge commit whose second parent is pre-staging,
and a conflicting direct push to staging stops the sync without pushing.

`checked_by` is null because the only thing left to check is whether a
session ran the command when it was asked to, and nothing in a tree
records that; what the command does once run is the harness case above.
