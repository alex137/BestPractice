---
title:         Very deep check — run record
kind:          record
status:        closed
opened:        2026-09-06
closed:        2026-09-07
superseded_by: null
supersedes:    []
audience:      session
summary:       "The run record of the very deep check: four ordered passes over every repository in force, and what each one found."
---
# Very deep check — run record

The state of the current [very deep check](../practices/very-deep-check.md),
and the ledger of the ones before it. The check is deliberately more than one
session's work, so a session picks up at the first pass below that is not
marked done rather than starting over. A pass is never quietly skipped: one
deliberately not run is recorded here as not run, with the reason.

**How to use this file.** A session starting or resuming a run fills in the
table, then records what each pass turned up under it: what was found, what
was fixed in the same pass, and what was deferred with the
[TODO.md](../TODO.md) line it went to. When the last pass is done, collapse
the run to one row under "Runs so far" and clear the table for the next one —
this document holds the run in progress, not an archive of every finding
([docs-are-current-state](../practices/docs-are-current-state.md); the
findings themselves live in the commits that fixed them and in
[TODO.md](../TODO.md)).

## Current run

**Started 2026-09-08**, on Morgan's direct request — a second full run
ahead of showing `precedent-beta-v01` to Alex, after several days of heavy
change (153 commits on the integration branch since the previous run
began). Scope: all four repos in force — `alex137/BestPractice`,
`themorgan/precedent-individual`, `themorgan/precedent-team-repo-maintenance`,
`themorgan/precedent-team-tms`. Working branch
`claude/deep-review-before-sharing-6zvsio` in each.

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | done | 2026-09-08 | fresh install rebuilt and clean; the UPDATE path built for the first time against a 372-commit-stale consumer and found the run's worst defect |
| 2 — mechanisms | done | 2026-09-08 | worked against the tools this run was itself using; three defects, each a confident wrong answer rather than a failure |
| 3 — coherence read | done | 2026-09-08 | whole-tree lint clean; acronyms cleared; one contradiction found between this practice's own checklist and a decision made that morning |
| 4 — catalogue and housekeeping | done | 2026-09-08 | branch verdicts recorded below; the private sets' own backlog is Morgan's call and is left to him, not guessed at |

**This run is COMPLETE.** No roadblock is open: every pass-1 and pass-2
finding below is fixed, pushed, and verified on origin by content rather
than by ref equality.

**What a next run should read first.** The previous run's note said the
most likely fourth defect was a fixture or tool reporting a *confident
wrong answer* rather than failing. That was right, and it is now the
run's dominant pattern rather than a single instance: **three of this
run's six defects are a guard written for the wrong failure mode.**
`git cherry` exits 0 and lies; `refresh` prints "nothing to do" over a
tree it has not cleaned; `seed` writes a manifest that has already
forgotten what it left behind. In each case a guard existed, read as
coverage, and could never fire. **When you find a guard, do not check
that it is present — check that its failure mode is the one that
actually happens**, and prove it by replaying the control against the
pre-fix code. Two of this run's three controls passed against the buggy
code on the first try; only rebuilding the fixture made them
discriminate, and one of them is now documented as NOT discriminating so
a later session does not over-trust it.

**Pass 1's newest step has now run for real, and what it found is open.**
The `BOOTSTRAP DRIFT` section — added 2026-09-11, after Morgan asked whether
the brand-new-adopter path was checked at all — regenerates each resolved
team and individual set with today's generator and diffs it against the real
thing. Run against all four live sets the same day, it found **two open
items, repeated in every set**: each set's vendored engine is an older
upstream vendoring (`precedent_vendor_engine.py refresh` is the whole fix,
and it is each set's own repository to change, not this one's), and
`commit-identity.sh` differs from canonical everywhere — the drift
[TODO.md](../TODO.md)'s `source-hook-drift` item already tracks, now
confirmed by a second, independent mechanism. Neither is fixed here: both
land in repositories under another owner, which a session rooted at this one
cannot push to.

The run also found a defect in the check itself, fixed the same day: it
printed 60 lines carrying about six facts, because an older vendoring
differs in every engine file at once. See the practice's Story.

### Prerequisites

All four repos proved current against origin before anything was read.
All four working branches existed only locally and were pushed first —
the tool refused the run twice, correctly, until they were.

The deep check suite was green before the passes began (130 passed, 0
failed; 30 passed, 0 violated) and green after them, with three new
checks registered.

**One prerequisite failed silently and is the run's most consequential
finding.** The session's hooks had never run — see pass 1.

### Pass 1 — adopter installs

**The fresh install is clean**, rebuilt from scratch per
[INSTALL.md](../INSTALL.md) §0 against the current tip: `0 violated`,
which is what that section promises. One apparent finding was **the
fixture's fault, not the install's** — skipping §0 step 5 left the repo
with no `MAP.md` and `orientation-map` correctly fired. Recorded because
the temptation to report it was real: a violation on a fixture reads as a
defect in the thing under test.

**THE SESSION'S OWN HOOKS NEVER RAN, and nothing said so.** The harness
rooted this session at `/home/user` — the parent of the four repos, which
is the layout Precedent's own source resolution *requires*, since a team
source resolves as a sibling clone. Every hook in
[.claude/settings.json](../.claude/settings.json) is written as
`$CLAUDE_PROJECT_DIR/.claude/hooks/…`, `/home/user` has no `.claude/`, so
every one of them resolved to nothing. Absent all at once: the commit
identity (`user.email` was still the container's bot, so every commit
would have been refused by this repo's own check), the global backstop,
the freshness guard, the package installs, the path-trigger channel, the
Stop-time git check, and `.precedent/SESSION_PRACTICES.md` — the only
route by which private practices reach a session. **53 practices that
bind work here were silently not in force**, `audience-register` among
them, which governs how every reply in the session is written. AGENTS.md's
Standing Instruction told the session to read a file that was never
generated. Fixed with
[tools/precedent_session_check.py](../tools/precedent_session_check.py),
which tests each guarantee by its *effect* and repairs with `--apply`; it
cannot be a hook, because the failure is that hooks do not run.

**The update path was built for the first time, and it was bricked.**
Every fixture before this one built a repo that never had to move. A
consumer vendored at a 372-commit-old commit and brought forward exposed
three compounding defects:

1. `refresh` runs the consumer's OWN vendored copy, which carries the file
   list it was vendored with — so the first refresh after upstream renames
   an engine file asks git for a path that is gone, and exited hard. Fixed
   upstream that morning in `d0b8fca`, **but that fix can only arrive
   through a refresh**, so every repo vendored before it needs one manual
   reseed to escape. Nothing said so; [INSTALL.md](../INSTALL.md) §2 step 6
   now does.
2. `seed` — that documented recovery — never called the cleanup at all,
   so it wrote a manifest that had already forgotten the old file while
   leaving it on disk, untracked by anything.
3. `refresh`'s early exit returned on a matching commit before any cleanup
   could run, and its completeness test looked only for *missing* wanted
   files, never *present unwanted* ones. The orphan was therefore
   permanent.

After (2) the file is in no list any mechanism consults — gone from
`KINDS`, gone from the manifest, and `_untracked_engine_files` is keyed on
the current lists by design. Hence `RETIRED_ENGINE_FILES`: a name, once
shipped, cannot be derived back out of the code that stopped shipping it.
All three practice sets were carrying a dead `precedent_retire_path.py`
with `status` reporting them healthy; all three are now refreshed onto the
current engine with the file removed, verified on origin.

**Not done in this pass**, and recorded as not run rather than skipped:
the migration fixture (the fresh-install and update halves were
prioritised, and the update half is where every defect was), the empty
neighbourhood, and the cross-repo permissions walk — the same walk the
previous run also left open. **No real consumer repository was attached**,
so pass 1 is PARTIAL on its highest-yield item for the second run running.

### Pass 2 — mechanisms

**Question 14 (does a verification enumerate, or sample) found the run's
first defect, in the very deep check's own tool.** The unlanded-work scan
reported three branches of `precedent-individual` as carrying 22 commits
of unlanded work. All three were plain ancestors of `main`. `git cherry`
on a shallow clone cannot find a merge base and answers by calling every
commit unique — exiting 0 while doing it. The guard written for exactly
this checked the exit code, so it could never fire. `git merge-base` is
the honest witness: it exits 1 where cherry exits 0. The direction is what
made it expensive: this section exists to tell a session which branches to
go read *before* the passes, so a fabricated count spends precisely the
reading it was built to save.

**The printer half mattered as much as the count.** `if
_r.get('unique')` folded an unmeasurable branch in with a measured zero
and then printed the all-clear — a confident result from a scan that never
ran.

**Question 8 (two of anything that should be one) — clean this run.**

**A regression, caught by the harness and worth recording.** Routing
`seed` through the new cleanup read the manifest via a helper that
`sys.exit()`s when there is none, which killed seeding into a fresh
repo — seed's primary case. Every fixture already had a manifest, so
nothing local caught it; the full harness run did, on the first attempt
after the change.

### Pass 3 — coherence read

**Whole-tree lint is clean**: no broken relative links, no skipped
heading levels, no accidental strikethrough, across every tracked
document.

**Six unglossed acronyms, all fixed** — `RPP` in five documents and `RAG`
in one, expanded on first use. Checked first that expanding was safe: the
full name is explicitly allowlisted in the private blocklist (Morgan,
2026-09-07: *"the name isn't private"*), so this is not a disclosure.

**A contradiction between this practice and a decision made that
morning.** Pass 3's "keywords with no entry" bullet named "Go merge" as
its own example of a phrase that must reach [GLOSSARY.md](../GLOSSARY.md)
via a practice's `defines:` field. Commit `eef671f`, earlier the same day,
cleared `defines:` on exactly those practices because Morgan said *"Don't
put it in the glossary."* **Following the bullet would have reversed
him.** The bullet now states the property as *findable*, not *in the
glossary*, and records the near-miss. This is the argument for reading
recent work before trusting a checklist written before it.

**Cross-source staleness — rolled out, not deferred.** All four attached
sources were behind; all are now on the current engine with views
regenerated and each repo's own checks at `0 violated`.
`precedent-team-repo-maintenance` was at `1 violated` before this run and is
not any more.

### Pass 4 — catalogue, backlog, and branches

**Branch verdicts**, evidence recorded, action left where it belongs:

- `alex137/BestPractice: claude/file-sharing-service-spec-0m9c7p` — 3
  commits, last moved 2026-07-26, adds a `share/` spec that exists nowhere
  on the integration branch. GitAround became a separate product on
  2026-08-14 and the practice engine is the plan of record, so this reads
  as superseded — **but that is Alex's repository and his call**, not one
  to make inside a review. Raise it with him.
- `precedent-individual: precedent/engine-refresh-c6c885033a9f` — **CLOSE.**
  It vendors `c6c885033a9f`, which is now an ancestor of what this run
  vendored into that set. Mechanically superseded; nothing is lost.
- `precedent-individual: claude/pre-launch-audit-fixes-7wumzx` (19
  commits) and `precedent-team-repo-maintenance: …` (16) — **CLOSED without
  merging, 2026-09-08, on Morgan's decision after this run put the
  evidence to him.** Both are far BEHIND `main`, not ahead of it: 83 and
  58 commits respectively, branched 2026-09-05. Their substance was
  re-done on `main` rather than merged, which is why `git cherry` still
  calls every commit unique — different patch-ids, identical content.
  Checked file by file rather than inferred: the `SOURCE_ROOT`/`ROOT`
  split, `my-identity-is-not-private.md` at the same 69 lines,
  `config.json.sample` at the same 15, the grandfathered-commit
  mechanism, the generated-header skip, `leak-blocklist.txt`,
  `test_no_stale_counts.sh`, and the whitespace-collapse fix in
  `check_derived_file_marker.py` are all on `main` already.
  **The one thing `main` lacks is the reason to close rather than
  merge**: the team branch carries a 93-line `practices/fail-gracefully.md`,
  and `main` has none because the 2026-09-07 run promoted that practice to
  universal, where it now lives at 157 lines. Merging would resurrect a
  team-level copy of a universal rule and re-create exactly the same-level
  collision that promotion ended.

  **A near-miss worth carrying forward.** The first reading of these
  branches was wrong in the opposite direction: `git diff main...branch`
  showed `my-identity-is-not-private.md` and `config.json.sample` as clean
  `+` additions, which reads as *"main does not have these"*. The three-dot
  form diffs against the 2026-09-05 MERGE BASE, not against `main` — so it
  answers "what did this branch add since it forked", which is a different
  question from "what does main still lack". Ask the second question with
  `git ls-tree main <path>` or by reading main's own copy; the three-dot
  diff will not answer it, and it fails in the direction that argues for
  merging superseded work.

**The private sets' own backlog was not swept this run.** Recorded as not
run, with the reason: their integration branch is `main`, this session is
confined to a working branch in each, and triaging another person's
backlog is not a review's job.

## Runs so far

| Run | Passes completed | What it changed |
|---|---|---|
| 2026-09-08 | 1, 2, 3, 4 | Ahead of showing `precedent-beta-v01` to Alex. Six defects, all fixed and pushed: the unlanded-work scan fabricating work on a shallow clone; `seed` and `refresh` between them leaving a renamed-away engine file in every adopter's tree, permanently; the withdrawn-practices table linking a successor that lives in another source, which failed a team set's own light-check; a session whose hooks never ran, so 53 private practices were silently not in force; the checkout being moved off its working branch mid-session (cause NOT found — detector added); and this practice's own pass-3 bullet instructing a session to reverse a decision Morgan made that morning. All three practice sets refreshed onto the current engine and their orphaned file removed. |
| 2026-09-07 | 1, 2, 3, 4 — all four | The first run to complete all four passes under this practice. ≈30 defects found and fixed across four repositories: 6 in pass 1, 8 in pass 2, the rest in passes 3 and 4. Shipped `internal_paths` and `output_paths` for headline scoping, two content-corruption fixes in `title_case.py`, the failure recap in `verify_harness.py`, a hermetic fixture, the merge-commit backstop, commit identity reaching every attached repo, the within-source conflict scan, and `tracked-practice-files`. Promoted `fail-gracefully` and `bold-key-phrases` to universal, ending two same-level collisions. Pass 4's 53 sequential judgments deliberately not run — see the closing note. |

The 2026-09-06 [pre-launch audit](PRELAUNCH_AUDIT.md) is the closest thing to
a prior run, and is where pass 1's method and all but one of pass 2's
questions come from — it was not run under this practice, and its own
still-open list is a separate document, kept there rather than copied here.
