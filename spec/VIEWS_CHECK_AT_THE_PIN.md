---
title:         The views check reads a shared set at the commit it was synced at
kind:          proposal
status:        drafted
opened:        2026-10-05
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "A consumer's views check compared its views against whatever branch a shared set's clone had checked out, so a set change Booked and not yet Produced refused every push, and the suggested sync rolled it back. Every sync now records the commit it read each set at; the check reads the set there, holds a push to the set's matching rung, and a sync refuses to roll a set back."
---
# The views check reads a shared set at the commit it was synced at

Written 2026-10-05, on `claude/views-check-at-the-pin-2026-10-05`, for
whoever picks this up without having been in the session that built it.

## The situation

A consuming repository declares shared practice sets
(`precedent-shared-writing`, say) that session start clones beside it, at
`../precedent-shared-writing`. The consumer's generated views (its
`practices/` tree, `tools/checks/`, shipped files, harness adapters,
`MANIFEST.json` and the loader block in its own AGENTS.md) are rendered from those
sets by [`precedent_sync_views.py`](../tools/precedent_sync_views.py), and
the push check's `views_sync` step runs it with `--check` on every push.

Everybody here works on the five-step ladder: a working branch is Booked
into `pre-staging`, Debuted into `staging`, Produced into `main`. A shared
set climbs its own ladder independently.

## What went wrong

On 2026-10-05 a consumer's session was refused on push twice in an hour, for
"drift" in files the push never touched: first Word-document changes to the
writing set (footer, margins, contents page, bullet indent), then a new
practice, `dated-download-names`.

The sequence both times:

1. A change to the writing set was Booked into the set's own `pre-staging`.
2. The consumer synced and took it into its own `pre-staging`. That is the
   ladder working as designed: each rung carries what passed the rung below.
3. The next session started. Session start leaves each set's clone on the
   set's `main`, which did not have the change yet.
4. The views check compared the consumer against whatever the clone had
   checked out, `main`, and reported every file the Booked change touched as
   drift.
5. The check's own remedy, a plain sync, would have rendered from that
   `main` and rolled the Booked change back out of the consumer. One session
   saw the diff do exactly that (the footer, Heading 1 and margin rules
   deleted, the header logo shrunk) and stopped.

The only ways through were to check the clone out at the set's `pre-staging`
by hand, or to Debut and Produce the set early. The consumer filed both a
gotcha and an open item.

A related misreport: [`precedent_session_check.py`](../tools/precedent_session_check.py) called a clone
deliberately checked out at the set's `staging` "2 commit(s) behind
origin/main and 6 unpushed commit(s) ahead". Those six were on GitHub, on
`staging`; they were only not on `main`.

## The options, and what was wrong with each

**A. Compare by rung** (the proposal handed over). When checking a consumer
branch, read each set at its matching branch (a working branch or
`pre-staging` at the set's `pre-staging`, `staging` at `staging`, `main` at
`main`), from origin refs rather than the clone's checkout.

Attacked: it still compares a committed snapshot against a moving target,
and only changes which target moves. The day another session Books a second
change into the set's `pre-staging`, every consumer's next push is refused
again, for the same files it never touched, until somebody syncs. The
refusal moves from Produce time to Book time, which comes more often: on
the day this was reported the writing set was Booked several times. The
remedy is safe now (a sync from the set's `pre-staging` takes the new
change rather than losing an old one), but it drags an unrelated set update
into every unrelated push. Rejected as the main mechanism; its rung mapping
survives below in a narrower job.

**B. Session start checks each set's clone out at the rung matching the
consumer's branch.** Attacked: one clone serves every repository in a
session, and they can be on different rungs. It also keeps the answer
depending on hidden local state, which is the root of the bug. Rejected.

**C. Skip set-owned files in the push check's views step.** Attacked: a
hand-edited materialized practice would pass on every rung, which is
exactly what the views check exists to catch. Rejected.

**D. Record what each view was built from, and check against that** (the
lockfile pattern). Every sync writes, in `MANIFEST.json`, the commit it read
each live set at. The views check reads each set at that commit, from a
throwaway worktree of its clone. "Are the committed views what their
recorded inputs produce?" then has one answer on every machine and every
branch, whatever the clone has checked out and however far the set has
moved. A hand-edited file still fails everywhere.

That separates the two questions the old check blurred, and each gets its
own remedy, neither of which can lose work:

- **The rung.** A push to `pre-staging`, `staging` or `main` may carry a set
  only at a commit the set itself has landed on that rung or above. A
  consumer's `main` never carries what the set has not Produced. The remedy
  printed is to Book, Debut or Produce the set, and it says in so many words
  not to sync. This is where option A's mapping lives: a narrow
  containment test, not the comparison target.
- **Freshness.** When the set's matching rung has content the consumer has
  not taken, the check prints a note, not a refusal. Taking it is a
  decision.

And the write side gets a guard: a sync refuses when the clone does not
contain the commit the consumer already carries, because syncing would
roll it back. The refusal names the exact `git checkout` that fixes it.

D was chosen. Attacking it turned up these holes, each closed in the code:

| Hole | Answer |
|---|---|
| A manifest written by an older engine records no commits | The commit is inferred: the clone's checkout, each rung's tip, then up to 300 commits of rung history, newest first, matched on the per-practice `source_sha256_16` hashes the manifest already records. The first sync on the new engine writes real pins. |
| The pinned commit is not in the clone (a stale or shallow clone) | Fetched by id, then by the rung branches. If still missing, the check says so and reads the clone as it stands, as before. |
| Session start leaves the set clones with uncommitted vendored-engine copies and a regenerated map file | "Uncommitted" counts only files a sync reads (`practices/`, `bootstrap/`, `tools/` minus the engine files `tools/ENGINE_MANIFEST.json` lists, `precedent-source.json`). Without this, no clone in a real session was ever pinned. |
| A sync and its own check disagreed when a clone had uncommitted changes in a file a sync reads (the individual set's `bootstrap/commit-identity.sh`, rewritten by session start) | A sync now always reads committed content: a clone with uncommitted changes in synced files is read from a worktree at its commit, and the sync says the changes were not taken. What a repository commits as its views has to be reproducible from commits. |
| A set's `main` carries the pull-request merge commits its `pre-staging` never gets, so a pin at `main`'s tip is "not on pre-staging" | A pin counts as landed on a rung when it is on that rung or any rung above it. |
| A full-tier pass recorded for `staging` would be reused for the same tree pushed to `main`, skipping the stricter rung | The destination goes into the views step's argv as `--for-branch`, so the two sign differently. Promote passes it with `--destination`. |
| A consumer's working branch may legitimately try a set's unbooked work | No rung refusal on a working branch; only the note. |
| A set that squash-merges would break ancestry | Today's Book, Debut and Produce all make merge commits. A set that squashed would see a rung refusal persist after promoting; that would be the place to add a content comparison. |

What D does not change: the practices a session follows still come from the
clone's checkout (the session's untracked practices file), and a set
repository's own views ([`build_views.py`](../tools/build_views.py), not a
materialize) never read a sibling set.

## What was built

- [`tools/precedent_source_pins.py`](../tools/precedent_source_pins.py),
  new: pins, inference, reading a source at a commit, the rollback guard,
  the rung test and the freshness note. `python3
  tools/precedent_source_pins.py --repo . [--branch B]` prints each pin and
  what the two tests say.
- [`tools/precedent_materialize.py`](../tools/precedent_materialize.py):
  `MANIFEST.json`'s `sources[]` entries record `commit` for a source read
  from a git checkout outside the repository. The manifest comparison
  ignores it, like the timestamp; the content it produced is compared file
  by file.
- [`tools/precedent_sync_views.py`](../tools/precedent_sync_views.py):
  `--check` reads at the pins; `--for-branch BRANCH` adds the rung test; a
  write refuses a rollback (`--allow-rollback` overrides) and reads
  committed content. The drift message no longer blames a set for moving on.
- [`tools/precedent_push_check.py`](../tools/precedent_push_check.py): the
  destination (from `--push-command`, highest rung first, or
  `--destination`) reaches the views step.
- [`tools/precedent_branches.py`](../tools/precedent_branches.py): Promote's
  four checks name where their result is pushed.
- [`tools/precedent_session_check.py`](../tools/precedent_session_check.py):
  "unpushed" means on no origin branch; commits on another origin branch
  are named by it and do not make the clone stale.
- [`tools/verify_harness.py`](../tools/verify_harness.py): three checks,
  `check_views_check_reads_a_set_at_the_commit_it_was_synced_at` (14
  cases, each direction the handover asked for), and
  `check_push_destination_reaches_the_views_check` and
  `check_session_check_names_commits_on_origin_off_main`.

Verified against the consumer that reported it, from scratch worktrees of
its `pre-staging`, `staging` and `main`: with the writing set's clone on
`main`, the old engine reported nine differences on `pre-staging`; this one
reads the set at the commit that matched (its `pre-staging`) and reports
only the three files every engine newer than the consumer's vendored copy
changes. A write sync from the clone on `main` was refused, and from the
clone at the set's `pre-staging` it changed no practice file.

## Rollout

These are vendored engine files, so the fix reaches a repository only
through its own Update Vendors. **Every consuming repository that declares
a shared set read from a sibling clone needs it**; that is where the
refusal happens. The first sync after the update writes the pins; until
then the check infers them. Practice sets get the session-check fix and
Promote's destination on their next Update Vendors; they do not need it
for this bug, because a set does not materialize another set.
