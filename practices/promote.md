---
slug:        promote
title:       "\"Promote\" moves pre-staging into staging, or staging into main, and says which first"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message says \"Promote\" about branch tiers, or asks to move pre-staging into staging or staging into main"
gates:       ["merge"]
index_clause: "pre-staging->staging or staging->main, chosen from the work; says which"
checked_by:  null
defines:     ["Promote", "pre-staging"]
command:     {"Promote": "Land this session's own unsaved work on pre-staging first, then move the next tier up -- pre-staging into staging, or staging into main, whichever the work just done needs -- saying which before it starts. The full check runs on the whole batch, and nothing moves unless it passes."}
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
  this looks great, let's do it, go ahead, go update\". Not re-running
  the suite on files that already passed it is his rule too (Morgan,
  2026-09-25: \"staging will not run the full suite of tests if it's being
  promoted from pre-staging to staging and the full suite of tests ran on
  pre-staging and nothing has changed\", strength: decided). Saving the
  session's own work with Go update before promoting is his rule too
  (Morgan, 2026-09-25, strength: decided)."
strength:    assented
---
## Rule
When a message says **"Promote"** about the branch tiers -- the whole
message, or a clause like "promote pre-staging" -- **first check this
session's own branch for work that is not on pre-staging yet**: anything
uncommitted, or committed but not yet landed. **If there is any, run
[Go update](go-merge.md) on it first**, which lands it on pre-staging, and
confirm `origin/pre-staging` carries it. Promote carries that authorization
itself: nobody is asked a second time. Only then run, in the repository the
work is in:

    python3 tools/precedent_branches.py --promote --work BRANCH

**Promote picks its own step, and says which before anything else.** It
moves pre-staging into staging, or staging into main, and its first line is
*"Now promoting from pre-staging to staging"* or *"Now promoting from
staging to main"*; the reply opens with that same line. The session decides
from the conversation and hands the tool what it knows (Morgan, 2026-09-26:
*"Promote should decide based on the context and ... what branch we were
just working on. If the promotion should be pre-staging to staging or
staging to main ... it should print that explicitly on the screen"*,
strength: decided):

- **`--work BRANCH`** -- the branch (or commit) this conversation was just
  working on. Not on staging yet: pre-staging into staging. Already on
  staging but not on main: staging into main.
- **`--to staging` or `--to main`** -- when the person named the step
  ("promote staging to main"). The name wins.
- **Neither** -- a bare Promote in a session that did no work of its own.
  Work waiting on pre-staging goes first; only when there is none does
  staging move into main.

A Promote that resolves to staging into main is the named go-ahead
[merge-target-is-beta-branch](https://github.com/alex137/BestPractice/blob/staging/local/practices/merge-target-is-beta-branch.md)
asks for, since Morgan asked for exactly this; nobody is asked again.

**Waiting for a Promote never keeps a session open.** Work on pre-staging
is already on `origin`, and any later session can promote it, so a pending
Promote is never a reason for "Don't archive this session" unless there is
a genuinely urgent reason to move it now ([the-boildown](the-boildown.md),
archive condition 2).

Promote moves what is on pre-staging, so work still sitting in the session
would otherwise miss the batch the person just asked to move (Morgan,
2026-09-25: *"If there is anything in that session's branch that is not yet
committed, to first do a 'go update' [which go into pre-staging] before
starting the 'promote'"*, strength: decided). Nothing to save means
nothing to do here: go straight to the command.

The command does the whole promotion, and a session adds nothing to it:

0. **Takes the Promote lock**, so only one window promotes at a time. The
   lock is the branch `precedent-promote-lock` on origin, which only ever
   moves forward: one empty `[skip ci]` commit per claim or release, the
   newest one saying who holds it. **If another window holds it, this
   Promote does nothing** and says so -- *"another window is promoting
   right now"* -- and that is the whole report: don't Promote again while
   it runs, and don't suggest it either. A claim left by a window that died
   frees itself after 15 minutes. The branch is never deleted (a session
   can't), and it is not unlanded work or a branch to tidy up.
1. **Copies down what reached staging or main by another route** -- a
   direct push to staging, a workflow's bot commit on main, an edit made on
   GitHub's website -- **once it has had its own tier's checks.** Staging's
   is the full local check; main's is that plus the GitHub test, where the
   repository has one installed. A published pass for the exact files
   counts; for main, so does a GitHub run on the commit itself or on the
   pull request that brought it in. **Whatever is missing, it runs** --
   the full check in a throwaway worktree, and for main the GitHub test by
   its `workflow_dispatch` button, waiting up to 30 minutes for the answer.
   What passes is merged into pre-staging. **What fails is not copied, and
   is reported** with the commit and the check: it is live on that tier
   already, so it is fixed the normal way, on pre-staging. **Merge commits
   that change no file are not drift** and are left alone -- every
   ordinary pull request into main leaves two. A conflict stops the sync
   before anything is pushed. It never pushes to staging or main. When
   nothing waits to be promoted but main or staging carries such work,
   Promote still runs this step and says so.
2. **Makes one merge commit of pre-staging onto staging** -- always a merge
   commit, never a fast-forward, so no pre-staging commit's `[skip ci]`
   line can become staging's head and silence the GitHub test on the pull
   request into main.
3. **Runs the full push check on exactly that commit**, in a throwaway
   worktree, and **pushes it to staging only if it passes.**
   **It does not run the suite a second time on files that already passed
   it.** When the full check already passed on exactly these files -- the
   usual case after a high-risk change, which ran it before landing on
   pre-staging -- that result stands and nothing is re-run, **whichever
   window ran it**: a pass is shared through origin, so Promote said in one
   window finds the run another window made. "Exactly" is
   the whole condition: one changed character anywhere, including a push
   made straight to staging in between, and the suite runs. It is what the
   files are that decides, never which branch they came from. **It says
   which happened**: "NOT re-run", with when the earlier run passed, or how
   long the run it just did took.

**Staging into main runs step 1 first, then the same full check** on staging merged into main
(standing on an earlier pass of the same files, as above), then pushes a
throwaway copy of staging, `to-main-DATE`, and stops: the tool never moves
main. The session opens the pull request from that copy into main, waits
for its GitHub test -- main's last gate -- and merges it with a merge
commit. Report the copy, the pull request and the merge, and confirm with a
fetch that `origin/main` carries staging's tip.

**Main takes staging by a pull request from a throwaway copy, never from
staging itself.** A merged pull request's page offers to delete its
source branch, and on 2026-09-26 staging, the source of the pull request
into main, was deleted right after that merge -- by what, is not
established ([the gotcha](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-09-26-a-pull-request-from-staging-deletes-staging.md)).
Promote makes that copy itself; the merge gate refuses a pull request
from a tier branch.

**Report what it printed, plainly**: the commits promoted and whether
the full check ran or stood from an earlier run, or -- on
`PROMOTE REFUSED` -- the failing check and the batch it was run on. A
refusal is fixed on pre-staging, like any other edit, and promoted again;
never by pushing the batch to staging some other way. When another window
promoted the same batch while this one was checking it, Promote says so and
exits cleanly -- *"another window promoted this batch while the check
ran"* -- and that is the whole report: the work is on staging, and there is
nothing to run again.

**Never suggest a Promote that another session is already running**, and
the same goes for `Go update` or a merge of the same pull request or the
same work: two windows doing one job race, and the loser throws away a full
check run. Before recommending one, look -- the pull request's state, the
branch tips, and any session this one knows is on the same work -- and when
another session has it, say that it does, not that the person should do it
again (Morgan, 2026-09-25, after two sessions promoted the same batch at
once: *"you should NEVER suggest to \"promote\" or \"go update\" or
\"merge\" when another session is already doing that with the same
PR/thing"*, strength: decided).

**It can take as long as the full check does** -- minutes in this
repository. Run it with a long timeout, or in the background, and keep
working; staging does not move until it is done, and nothing else waits on
it.

**Not practice promotion.** Moving a practice *candidate* into the
catalogue is also called promotion, and a message about a candidate or a
practice means that step, which has its own tool. This command is about
branches, never a practice.

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
[spec/BRANCH_TIERS_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/BRANCH_TIERS_PLAN.md).

## Install
Nothing to install beyond the engine: [precedent_branches.py](../tools/precedent_branches.py) ships in
every kind's engine files. Its behaviour is pinned by [verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py)'s
`check_promote_pre_staging` -- a failing batch leaves staging where it was,
a passing one lands as a merge commit whose second parent is pre-staging,
and a conflicting direct push to staging stops the sync without pushing;
and by `check_sync_copies_work_from_above_once_checked` -- work from main or
staging is copied down only once checked, a failure is reported and never
copied, and merge commits that change no file are left alone.

`checked_by` is null because the only thing left to check is whether a
session ran the command when it was asked to, and nothing in a tree
records that; what the command does once run is the harness case above.
