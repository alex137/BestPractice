---
slug:        promote
title:       "\"Promote\" moves pre-staging into staging, or staging into main, and says which first; \"Promote N\" does stage N of the five-stage ladder"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A phrase in a MESSAGE, like go-update's and push-directly's entries -- no file path reaches it. Routed by the `merge` gate. Decided: 2026-09-25, when the practice landed."
occasion:    "a message says \"Promote\", \"Promote N\" or \"Graduate\", or asks to move work up a tier"
gates:       ["merge"]
gates_why:   "Promote is the merge of pre-staging into staging -- the moment that gate exists for."
index_clause: "pre-staging->staging or staging->main, chosen from the work; says which"
checked_by:  null
defines:     ["Promote", "pre-staging", "Promote N", "Graduate", "the five stages"]
command:     {"Promote": "Land this session's own unsaved work on pre-staging first, then move the next tier up -- pre-staging into staging, or staging into main, whichever the work just done needs, and pre-staging into staging when both have work waiting -- saying which before it starts. The whole batch gets the checks of the branch it is entering -- the full local check going into staging, that plus the GitHub test going into main -- and nothing moves unless they pass. \"Promote N\" does stage N of the five-stage ladder: 1 Consider, 2 Act, 3 Booked, 4 Debut, 5 Produce.", "Graduate": "The same as **Promote**."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-25"
approved_by: "Morgan, 2026-09-27 (decided) -- never recommend a Promote
  another window is already running; Morgan, 2026-09-25 -- the three branch tiers are his own
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
  (Morgan, 2026-09-25, strength: decided). An ambiguous Promote -- both
  steps with work waiting -- moves pre-staging into staging (Morgan,
  2026-09-26: \"if my 'promote' is ambiguous and you don't know which of
  the two types of promotion it should refer to - then choose to do
  pre-staging to staging\", strength: decided). \"Graduate\" as a second
  word for the same command is his too (Morgan, 2026-09-26: \"Let's add a
  new vocab word 'graduate' to be used as a synonym for 'promote'\",
  strength: decided); \"Promote N\" and the five stages, 2026-09-27/28
  (spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md, strength: decided)."
strength:    assented
---
## Rule
**The five stages.** Promote is also the one word for the whole ladder a
piece of work climbs, from idea to production -- **"Promote N" does stage
N**, and each stage has its own word and a synonym:

| # | Stage | Synonym | What happens | Practice |
|---|---|---|---|---|
| 1 | **Consider** | Plan | Decide how much plan the work needs, and make that much. | [consider](consider.md) |
| 2 | **Act** | Build | Build it on this session's feature branch, pushed so it survives. | [act](act.md) |
| 3 | **Booked** | Shared Save | Move it from the feature branch to the landing branch (pre-staging). Also **Go update**, **Book it**. | [go-update](go-update.md) |
| 4 | **Debut** | Test Readiness | Promote pre-staging into staging, full checks. | [debut](debut.md) |
| 5 | **Produce** | Make live | Promote staging into main -- production -- full checks plus the GitHub test. | [produce](produce.md) |

The ladder is **optional for everyone**: anyone may use its words, nobody
has to, and a repository without pre-staging simply has fewer stages. A
person's own individual set may require it for them.

- **Read back every stage before it runs**, with its number, word and
  synonym and the repository and branches: *"Now Promote 4: Debut, Test
  Readiness -- moving pre-staging into staging (BestPractice)."* A request
  covering several stages names them all: *"Now Promote 3 then 4: ..."*.
- **Read the request, never scan it for a word.** Every stage word is
  ordinary English. The same step can be asked for many ways -- "Debut",
  "Promote 4", "promote pre-staging to staging", "move BestPractice staging
  to main" -- and a named step wins over any guess. Stage 5, which changes
  production, is read most strictly.
- **A bare Promote means the next step this work has not done, and never
  skips one.** Between possible moves, take the lowest: work on the feature
  branch means Booked first; pre-staging and staging both waiting means
  pre-staging into staging (below). Asking for a higher stage runs the
  lower ones first, and a bare Promote never sends finished work back to
  Consider.
- **"Graduate" is another word for Promote.**

The rest of this Rule is stages 4 and 5 -- the moves between branch tiers.

When a message says **"Promote"** about the branch tiers -- the whole
message, or a clause like "promote pre-staging" -- **first check this
session's own branch for work that is not on pre-staging yet**: anything
uncommitted, or committed but not yet landed. **If there is any, run
[Booked](go-update.md) (`Go update`) on it first**, which lands it on pre-staging, and
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

**When both steps have work waiting, a Promote is ambiguous, and it moves
pre-staging into staging.** Pre-staging has commits staging lacks, and
staging has commits main lacks: unless the person named the step, that is
pre-staging into staging, even when the work just done is already on
staging and waiting for main (Morgan, 2026-09-26: *"if my 'promote' is
ambiguous and you don't know which of the two types of promotion it should
refer to - then choose to do pre-staging to staging"*, strength: decided).
A later Promote carries it on into main.

A Promote that resolves to staging into main is the named go-ahead
[merge-target-is-beta-branch](https://github.com/alex137/BestPractice/blob/staging/local/practices/merge-target-is-beta-branch.md)
asks for, since Morgan asked for exactly this; nobody is asked again.

**Never recommend a Promote that another window is already running.**
When a Promote finds the lock held, or the reply gate reports one under way,
no reply suggests promoting that repository again -- not as a next step,
not as a plain line in The Boildown, not as "try again later". It says, at
most, that one is running, and which session holds it when that can be told
(Morgan, 2026-09-27, strength: decided: *"NEVER recommend a promote when
another session is already doing it!!!"*).

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
   can't), and it is not unlanded work or a branch to tidy up. **The merge
   gate takes the same lock** while it checks a pull request into staging
   or main (`hold_for_landing`; Alex, 2026-09-30: *"Do all three recs"*,
   strength: decided), so a Promote and a landing never move a tier under
   each other's check: whichever finds it held waits, and a claim naming
   "landing pull request #N" is a landing, not a Promote.
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
main. **That stop exits 3, not 0**, and its block opens with *"MAIN HAS NOT
MOVED YET"*: exit 0 from Promote means the branch it names has moved, so a
3 means the work below is still owed (2026-09-28: a session read the old
exit 0 as done while main had not moved). The session opens the pull request from that copy into main, waits
for its GitHub test -- main's last gate -- with
`python3 tools/precedent_branches.py --wait-main-test COPY` (exit 0 only on
a pass; never a poller of the session's own, since one crashed mid-wait on
2026-09-27), and merges it with a merge commit. Report the copy, the pull request and the merge, and confirm with a
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
the same goes for Booked (`Go update`) or a merge of the same pull request or the
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

**The one-line summary named the check loosely until 2026-09-26.** It said
"the full check", and Morgan asked whether that meant the check of the
branch the work enters. It always did -- the Rule above runs staging's
checks into staging and main's into main -- so only the summary changed, to
say so.

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
