---
title:         One command for Update Vendors
kind:          proposal
status:        accepted
opened:        2026-09-27
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Update Vendors becomes one tool run in the consuming repo: it does every step the runbook describes that needs no judgment, and stops once, with a single Left-for-you list of the calls that really are this repo's. The runbook shrinks to: run it, review the list, then Go update's chain. A decision upstream has already made ships as a step in the tool, never as prose a session has to find and apply by hand."
---

# One command for Update Vendors

**The problem.** "Update Vendors" is a phrase, not a program. It authorizes
the whole update, and then a session carries out
[vendor-update-runbook](../practices/vendor-update-runbook.md) by hand: twelve
steps across several tools, in a file over seven hundred lines long that each
session reads from the top. Every step a session performs by hand is a place
it can stop. Every consuming repo stops at the same places, because they all
run the same runbook.

The case that prompted this, 2026-09-27: a consumer update refreshed its
engine to `main` and then stopped. Its catalogue pin in
`process/manifest.json` still named `precedent-beta-v01`. The runbook said to
repoint it "in this same update", and Morgan had decided that on 2026-09-25.
But the repoint was a hand edit to the file that says which branch the repo
tracks. Claude Code's permission check held that edit for a human, so Morgan
was asked to re-make a decision he had already made. Runbook step 4 also
still sent a pinned install to the manual mirror, with no exception for
`main`, so the session went looking for a route it didn't need. The
engine refresh now does that repoint itself (same day), and step 4 is
corrected. This plan is about not having the next such bump.

**Status, 2026-09-27: built, all but the last two build steps.**
[tools/precedent_update.py](../tools/precedent_update.py) runs steps 1 to 4
and 6 of the shape below, with the three outcomes, and
[tools/checkin.py](../tools/checkin.py) takes `--repo`. The runbook and the
"Update Vendors" command now point at it. Still open: moving the
private-source reach and source-name checks (runbook steps 7 and 8) into the
tool, and the check that the runbook and the tool agree (build steps 3
and 5).

**Morgan, 2026-09-27** (`strength: decided`): *"For 3 i love it let's do it"*,
in answer to "one command for the whole update ... that ends with a short
'Left for you' list — only the conflicted files."

## The Rule This Plan Follows

**An upstream decision that changes a consumer's files ships as a step in
the tool, never as a sentence in the runbook.** The runbook is for the calls
that belong to one repo. Everything else is code, and runs the same way
everywhere. A session that finds itself editing a file because the runbook
told it to is looking at a missing tool step.

## The Shape

One command, run from the consuming repo:

    python3 <source-clone>/tools/precedent_update.py --repo .

**It runs from the SOURCE clone, not from the vendored copy.** That solves the
self-update problem the engine refresh works around with a second pass: the
tool doing the update is always the current one. It also removes the trap
that made today's fix awkward. [`checkin.py`](../tools/checkin.py) reaches a consumer through the
vendored catalogue, so a fix to it never runs in the repos that need it most.
Driven from the source clone, every step runs the current code.

In order, with no questions in between:

1. **Source clones current** against the pinned branch
   (`precedent_refresh_sources.py --apply`, which already refuses to report
   success when it could not do this).
2. **Engine refresh**, both passes, including the catalogue-pin repoint.
3. **Catalogue update** ([`checkin.py update`](../tools/checkin.py)), run from the source clone
   against `--repo`. Today `checkin.py` finds the repo from its own location,
   `git rev-parse --show-toplevel` from where it sits, so it needs a `--repo`
   argument first. That is the one prerequisite this plan knows of.
4. **Views regenerated** (`precedent_sync_views.py --repo .`).
5. **The mechanical sweeps the runbook lists as separate steps**: legacy
   leftovers, the todo migration when the tool has just arrived, the
   private-source reach check, the source-name check. Each one already
   exists; the runbook currently asks a session to remember to run it.
6. **The deep check**, this repo's own.
7. **One report**, and only one:
   - **Done**: what moved, from which commit to which, and that nothing is
     left. Exit 0. The session commits and runs Go update's chain.
   - **Left for you**: each item the tool would not decide, with the file,
     what differs, and the question. Exit 1. These are the conflicted-file
     reviews (a `DIVERGED` bootstrap or [`AGENTS.md`](../AGENTS.md) section, a `LOST` line,
     a decline to re-decide) and the add-or-drop-a-source question from
     step 9. Nothing else goes on this list.
   - **Failed**: a step could not run, named, with what was written before
     it stopped. Exit 2.

**It does not commit, push or merge.** Those stay with the session, under
Go update's chain as today. The tool writes files and reports. That keeps
the authorization where it already lives.

## What Changes for a Session

The runbook's working part becomes three lines: run the command; work the
Left-for-you list under the conflicted-file review that already heads the
runbook; then run Go update's chain. The history and the reasons each step
exists stay in the runbook, below that, for the session that needs to
investigate. They are no longer the procedure.

## Build Order

1. **`checkin.py --repo`.** The prerequisite. On its own it changes nothing
   for anyone.
2. **`precedent_update.py` driving steps 1 to 4 and 6**, with the three
   outcomes and one consolidated Left-for-you list (the engine's
   `_LEFT_FOR_YOU` is the start of it).
3. **Step 5's sweeps moved in**, one at a time, each deleted from the
   runbook's procedure in the same commit that makes the tool do it.
4. **Runbook shrunk** to the three lines above plus the reference sections.
5. **A check that the two agree**: a runbook step that tells a session to
   edit a file by hand, where the tool has a step that does it, is refused.
   What that check can mechanically recognise is still to be worked out;
   until it exists, a review of the runbook against the tool's step list is
   part of step 4.

Each step ships through the engine, so a consumer gets it on its next
refresh. The source-clone invocation means a consumer never has to be
updated to *receive* the updater.

## Not in This Plan

A fleet-wide "which of my repos are behind" roll-up. That is item 3 of
[todo-2026-09-21-nothing-checks-a-consumer-against-upstream](../todo/todo-2026-09-21-nothing-checks-a-consumer-against-upstream.md),
and needs cross-repository reach this tool does not.
