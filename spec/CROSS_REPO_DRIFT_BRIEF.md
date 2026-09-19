---
title:         Cross-Repo Drift Brief — precedent-individual and precedent-team-writing
kind:          brief
status:        open
opened:        2026-09-19
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       What a BestPractice-rooted session found and fixed for the 2026-09-16 todo/gotcha migration's dropped archive item, and what it found but could not fix — a misattributed practice link in precedent-individual and a batch of stale-anchor prose in precedent-team-writing — because both repos are outside its access.
---
# Cross-Repo Drift Brief — precedent-individual and precedent-team-writing

Written for a session that will be rooted in `precedent-individual` and
`precedent-team-writing` (Morgan's own private practice sets), picking up
where a BestPractice-rooted session had to stop. Assume no prior context.

## Background

This repository (`alex137/BestPractice`, on branch `precedent-beta-v01`) is
the public, universal upstream of a multi-repo practice-engine system
called Precedent. Several private sibling repositories vendor its engine
and/or contribute their own layer of practices:

- `precedent-individual` — Morgan's personal practice set (private, owner
  `themorgan` on the evidence in this repo's own
  [`record/stale_branches.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/stale_branches.md)
  and [`AGENTS.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md)).
- `precedent-team-writing` — a shared team practice set, "the craft of
  writing and formatting prose for a human reader" (private, same owner).
- `precedent-team-repo-maintenance` — a shared team practice set, "how to
  run and maintain a repository that vendors this practice layer" (private,
  same owner). Referred to below as **the pack repo**.
- `precedent-team-working-style` — a shared team practice set (private,
  same owner), not implicated in what follows.

A BestPractice-rooted session cannot write to any of these — this
session's tool access is scoped to `alex137/bestpractice` only, and the
repos are cloned locally read-only (by the environment's SessionStart
hook) as practice *sources*, not as work trees this session may push from.

## What Started This

An earlier session, also rooted in BestPractice, ran an "engine refresh"
and reported: 4 pre-existing violations in `precedent-individual`
("4 practices no longer resolve") and 21 in `precedent-team-writing`
("21 stale internal TODO.md anchors baked into its materialized practice
text"), said both predate its own work, and said neither is fixable from
inside BestPractice. It filed that as a TODO item and stopped there.

Morgan then asked the next BestPractice session (this one) to actually fix
it, noting the missing pieces might be found in a pack repo rather than
genuinely gone.

## What Was Investigated, and What Was Confirmed

**The exact "4" and "21" counts could not be reproduced from BestPractice.**
Running `precedent_resolve.py --strict` and `precedent_check.py
--full-sweep` natively inside both `precedent-individual` and
`precedent-team-writing` (as they stand today, with their own currently
vendored copy of the engine) comes back clean — 0 violated in both. The
most likely explanation is that the "engine refresh" session was running a
newer version of `tools/precedent_check.py` than either repo has vendored
yet, and that check's tree only exists as `precedent_check.py`'s own
`ROOT` (resolved from the running script's file location, via `git
rev-parse --show-toplevel`) — it cannot be pointed at another repo's tree
from outside it. Reproducing the exact counts needs a session actually
rooted in each repo, ideally after it has run "Update Vendors" to pick up
whatever new check the other session was using.

**One concrete instance of each kind of violation was found and confirmed
by direct inspection**, independent of the check tooling:

### 1. BestPractice's own gap — found and fixed here

`precedent-team-writing/TODO.md` (its item 4,
`todo-gotcha-stale-reference-exempted`) names a stale link to
`https://github.com/alex137/BestPractice/blob/precedent-beta-v01/TODO.md`,
anchored on `source-checks-adopt-engine-helpers`,
and says: *"that item is gone from BestPractice's current `todo/` tree and
its own `spec/TODO_GOTCHA_MIGRATION_MAP.md`, and nothing found here
confidently says where it went... Blocked-on: tracing the real destination
... in BestPractice."*

Tracing it in BestPractice's own git history confirmed the item (`TODO.md`
item 51, "Move the two private practice sets' checks onto the engine
helpers added 2026-09-10") existed, marked `DONE 2026-09-10`, in the commit
immediately before the 2026-09-16 migration (`9a08363b`) — but the
migration dropped it instead of writing the `status: done` file its own
plan ([`spec/OPEN_ITEM_AND_GOTCHA_PLAN.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
Part 4.1, step 2) calls for. It
had no row in the migration map and no file under `todo/` or
`todo/CLOSED.md`.

**Fixed in this session, committed and pushed to `precedent-beta-v01`**
(`38bd9c96`):
- [`todo/todo-2026-09-10-source-checks-adopt-engine-helpers.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/todo/todo-2026-09-10-source-checks-adopt-engine-helpers.md) — the
  restored archive, recreated verbatim from `git show 9a08363b^:TODO.md`.
- [`spec/TODO_GOTCHA_MIGRATION_MAP.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/TODO_GOTCHA_MIGRATION_MAP.md) — added
  the missing `source-checks-adopt-engine-helpers` row.
- [`todo/CLOSED.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/todo/CLOSED.md) — regenerated.

**This closes the "blocked-on" for `precedent-team-writing`'s item 4.** A
session rooted there can now repoint its stale link to
[`todo/todo-2026-09-10-source-checks-adopt-engine-helpers.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/todo/todo-2026-09-10-source-checks-adopt-engine-helpers.md)
and drop the `not_binding` exemption for that finding in
`precedent-team-writing/precedent.json` (it may still need to stay
exempted for the file's other flagged string, the instructional
`` `TODO.md` `` + `` `#slug` `` placeholder near the top of that same `TODO.md` — that
one was never a real link and needs no fix, only a judgment call about
whether the exemption should narrow).

### 2. `precedent-individual` — a link into the wrong repo (one of the "4")

`precedent-individual/practices/my-identity-is-not-private.md`, near line
36, reads:

```
**the names of my private repositories**, which is a different rule with
its own gate — see
[private-repo-scrub](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/private-repo-scrub.md).
```

`private-repo-scrub.md` has never existed in BestPractice (confirmed: no
commit in this repo's full history ever touched that path). It exists in
**the pack repo**, `precedent-team-repo-maintenance/practices/private-repo-scrub.md`
— confirmed on disk, and confirmed a second way: this BestPractice
session's own `.precedent/SESSION_PRACTICES.md` (generated at session
start from the sources this account's config declares) resolves
`private-repo-scrub` from that same pack repo.

BestPractice's own [`practices/practice-links-travel.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/practice-links-travel.md) already states the
rule this link breaks: *"From a PRIVATE source, drop the link markup and
keep the backticked path — an absolute URL would publish the private
repository's name into every consumer that materializes the practice...
Nothing downstream will repair that one, and nothing downstream should."*
`precedent-team-repo-maintenance` is a private source, so the correct form
is not a link into BestPractice (wrong repo) and not a link into the pack
repo either (would leak that repo's name into anything that materializes
this file) — it is the bare backticked slug.

**Proposed fix**, in `precedent-individual/practices/my-identity-is-not-private.md`:

```diff
- **the names of my private repositories**, which is a different rule with
- its own gate — see
- [private-repo-scrub](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/private-repo-scrub.md).
+ **the names of my private repositories**, which is a different rule with
+ its own gate — see `private-repo-scrub`.
```

**Not yet done:** confirming this is the only one of the "4," or finding
the other three. A targeted search of every absolute-URL-into-BestPractice
link and every bare-slug reference in `precedent-individual/practices/*.md`
turned up only this one broken case among six URL-style links total,
before the search had to stop for lack of write access to verify further
against a possibly newer engine.

### 3. `precedent-team-writing` — stale migration-era prose (part of the "21")

Seventeen files under `precedent-team-writing/practices/` — every practice
moved there from `precedent-team-repo-maintenance` in the 2026-09-09
subject split — carry an identical closing sentence in their "Moved to..."
provenance note:

> *"its TODO.md has since moved that content into per-item files, so the
> old anchor no longer resolves"*

Files: `trim-prose.md`, `draft-marker.md`, `list-restraint.md`,
`resolved-issue-note-updates.md`, `content-subdirs.md`,
`sensitive-characterization-scrub.md`, `list-item-parity.md`,
`brainstorm-citations.md`, `rule-links.md`, `push-back.md`,
`file-mention-links.md`, `deliverables-carry-no-process.md`,
`doc-recipe.md`, `proportional-emphasis.md`, `durable-list-anchors.md`,
`branch-links.md`, `no-stale-counts.md`.

This sentence is descriptive prose (explaining why an old anchor it does
not itself cite would no longer resolve), not a literal `TODO.md` anchor
link — `precedent_check.py`'s `todo-gotcha-stale-reference` check would not
flag it, and did not when tested. Whether this is part of what the other
session counted as "21 stale internal TODO.md anchors," and whether the
sentence is even still accurate as written (it depends on claims about
`precedent-team-repo-maintenance`'s own TODO.md history that this session
did not verify), is unresolved. **This needs a read of each file's full
context and a decision about whether the sentence should be reworded,
not a mechanical find-and-replace** — flagging it here rather than
guessing at a fix.

The same phrase also appears in three files in
`precedent-team-working-style/practices/` (`small-calls.md`,
`nonblocking-questions.md`, `quiet-checks.md`) and two in BestPractice's
own `practices/` (`push-back.md`, `small-calls.md` — these are the
deduplication stubs left behind by the same split, and are BestPractice's
own to fix if they need it; not touched in this session since they weren't
what was asked).

## What Repos the Fix Needs

- **`precedent-individual`** — write access, to fix item 2 above
  (`my-identity-is-not-private.md`) and to re-run `precedent_check.py
  --full-sweep` / `precedent_resolve.py --strict` there with a freshly
  vendored engine, to find the other three of the "4."
- **`precedent-team-writing`** — write access, to repoint the now-resolvable
  link in its `TODO.md` item 4, decide on and fix the 17 stale-prose files
  in item 3, and re-run its own full check to find the rest of the "21."
- **`precedent-team-repo-maintenance`** — read access is enough; it is only
  needed as a reference, to confirm where a practice like
  `private-repo-scrub` actually lives before assuming it is simply missing.

## Proposed Solution, in Order

1. In `precedent-individual`: apply the one-line fix in item 2 above; run
   "Update Vendors" to pick up whatever newer check produced the original
   "4" count, then `precedent_check.py --full-sweep` and
   `precedent_resolve.py --strict`; fix whatever else those surface, checking
   the pack repo before concluding anything is genuinely missing.
2. In `precedent-team-writing`: repoint `TODO.md` item 4's link to
   BestPractice's restored archive file (URL above) and reconsider its
   `not_binding` exemption in `precedent.json`; decide on and fix the 17
   files in item 3; run "Update Vendors" and its own full check for the
   rest of the "21."
3. Report back (or close the loop with Morgan directly) once both repos'
   checks come back clean.
