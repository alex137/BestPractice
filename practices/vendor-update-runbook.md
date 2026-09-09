---
slug:        vendor-update-runbook
title:       Taking an upstream update into a vendored tree
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message says \"Update Vendors\", or an upstream update is being taken into a repo that vendors a practice layer"
gates:       ["merge"]
index_clause: "\"Update Vendors\" -- refresh the source clone first; both layers move separately"
checked_by:  null
defines:     ["Update Vendors"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan"
---
## Rule
**"Update Vendors" is the phrase that asks for this**, and it authorizes the
whole sequence below without asking again -- the same standing-phrase
mechanism as [go-merge](go-merge.md), for the other operation a person
otherwise has to spell out every time. It does NOT authorize merging or
publishing what the update produces; that is still `Go merge`'s to give.

A vendored tree is updated by a fixed sequence, in this order, because
every step's answer is wrong if the one before it was skipped.

1. **Make the SOURCE clone current first, against the branch this repo is
   pinned to** — not the source's default branch. A stale source makes
   every later step confidently wrong: the diff is against the wrong
   lineage, and "already up to date" is the answer you get.
2. **Read every vendored layer separately.** A repo usually vendors more
   than one — the loader *engine* and the practice *catalogue* are
   different trees with different manifests, and **they move
   independently**. Checking one and reporting "current" is the common
   failure.
3. **Refresh the engine.** Expect two passes when the tool replaces
   itself; the second is not a retry, it is the new copy running its own
   corrected file list.
4. **Take the catalogue update by the documented route.** Under a branch
   pin this is the manual mirror, never a tool that resolves the remote's
   *default* branch — that mirrors the wrong lineage over a pinned tree,
   which is a wholesale revert wearing an update's clothes.
5. **Regenerate the generated views in the same change.** A refreshed
   generator whose output has not been re-run leaves the repo's committed
   views describing the old engine, and its own `--check` then fails on
   work that is otherwise correct. The bump and its output land together.
6. **Run this repo's own full check**, not the upstream's.
7. **Check that this environment can still reach its PRIVATE sources**,
   before you call the update done. A vendor update is when a new engine
   file arrives that the environment may not be configured for, and it is
   the one moment somebody is looking at how this repo gets its practices
   at all. Run
   [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py);
   `MISSING` means a source is absent and no credential is set, so the
   session is running on the universal catalogue alone and nothing else
   will say so.
8. **Verify by content on the remote**, never by ref equality
   ([verify-postcondition](verify-postcondition.md)).

**A refusal naming a file that no longer exists upstream means reseed, not
investigate.** The refresh runs *this repo's own vendored copy* of the
vendoring tool, which carries the file list it was vendored with — so the
first refresh after upstream renames or drops an engine file asks for a
path that is genuinely gone.

## Detail
**Step 1 is first because it is the one nobody thinks of as part of the
update.** The instinct is to start with the command that does the
vendoring. Every failure mode below step 1 is silent — no error, just an
answer computed against the wrong tree.

**On what "up to date" means for the source clone.** Fetch the pinned
branch by name. A clone can be current on its default branch and many
commits behind the branch that actually matters, and a shallow clone will
report divergence that does not exist — deepen before believing any
comparison.

**Never hand-edit a vendored file to resolve a merge.** The vendored tree
is not this repo's to change: restore it to what the manifest records and
re-run the refresh. A hand-edit is detected as drift and refused, and
`--force` is the wrong answer to that refusal — it discards the guard
rather than the edit.

## Why
An update is not one operation, it is a small pipeline where each stage
consumes the last stage's output. Run out of order it does not fail, it
produces a confident, wrong result — and a vendored tree that is silently
wrong is worse than one that is obviously stale, because nothing will
prompt anyone to look again.

## Story
**The phrase was chosen 2026-09-08**, by Morgan, in the same conversation
that moved `go-merge` and `park-it` up to universal: *"Let's use the phrase
'Update Vendors' to trigger vendor-update-runbook."* It is plural on
purpose -- a repo usually vendors more than one layer, and the step people
skip is the second one.

**Asked for by Morgan, 2026-09-08**, after watching a session do this from
memory across four repositories: *"maybe we define another phrase ... with
the general instructions on how to update the vendored in files? (Starting
with make sure your local copy of your main repo is up to date etc)."*

Every step here is a failure somebody already paid for. A consumer went
**167 commits behind** with the practice meant to catch it never firing,
because a branch pin had disabled both of its delivery paths for the same
honest-looking reason and neither knew about the other. A different repo
was told "up to date" by a check that only ever compared generated files
against declared sources — a real check, answering a different question
than the one being asked of it. A sync tool that resolved the remote's
default branch would have mirrored `main` over a beta-pinned tree. And on
the day this practice was written, three practice sets could not refresh at
all: upstream had renamed an engine file, and each set's own vendored copy
of the vendoring tool still asked for the old path.

**The phrase this began as is deliberately not here.** A keyword is one
person's preference, and a universal rule telling every adopting repository
to go invent a keyword of its own is exactly what got
`merge-authorization-keyword` retired on 2026-09-07. The procedure is
universal; the word that triggers it belongs in an individual set.

## Install
Before starting, name the layers this repo vendors and where each records
its provenance — usually a manifest per layer. If you cannot name them, you
cannot tell whether the update is complete, and step 2 is the step that
most often gets skipped.

Then run the sequence above, and report which layers moved and which did
not. "Updated" without naming the layers is the report that hides half a
job.

Step 7 runs itself: [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
prints the same line after a `refresh` or a `status`, so an update made
without reading this file still surfaces a source nobody can reach
(practice: checkable-gets-checked). Asked for by Morgan, 2026-09-09, in the
thread that found a whole session running with no team or individual
practices in force and no error anywhere.
