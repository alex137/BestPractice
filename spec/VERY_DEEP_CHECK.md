---
title:         Very deep check — run record
kind:          record
status:        closed
opened:        2026-09-19
closed:        2026-09-19
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

**Started and finished 2026-09-19**, on direct request ("very deep check"),
not time-boxed in words but kept mechanical by choice: no explicit consumer
attached and no full catalogue read, consistent with every prior run.
Scope: this checkout on `precedent-beta-v01`, worked on
`claude/charming-babbage-ypapbx`; the individual set and the three team
sets were refreshed to the current engine and read by the tool, not
written (every one probes `HANDOFF` from here — this session holds no
credential for `themorgan/precedent-individual` or any
`themorgan/precedent-team-*` repo — and their refreshed working trees were
left for their own sessions to publish).

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | not run | 2026-09-19 | no consumer rehearsal attempted this run |
| 2 — mechanisms | done (PARTIAL) | 2026-09-19 | mechanical only: `verify_harness.py` (214 passed, 1 real failure + 1 planted fixture), `precedent_check.py`, `doc_lint.py`, `doc_sync.py`, `leak_gate.py`; the tool's own sections read, not each tool against its own description |
| 3 — coherence read | not run | 2026-09-19 | no read of the practice catalogue or recently changed documents beyond what pass 2's tools cover mechanically |
| 4 — catalogue, backlog, branches | done (PARTIAL) | 2026-09-19 | the tool's branch, base-drift, unlanded-work and documentation-currency scans read; verdicts NOT assigned to any of the 238 branches the tool lists (13 carry unlanded work across every repo in force, 8 of them in this checkout, 4 hundreds of commits deep — see below); full catalogue read still not done |

**One real defect found and fixed; one real blocker found and left for a
decision.** What the run found and did:

- **`record/stale_branches.md` (pass 4's own generated branch report)
  carried no lifecycle frontmatter**, failing `document-status-header` in
  both `precedent_check.py` and `verify_harness.py`. Fixed in
  [tools/very_deep_check.py](../tools/very_deep_check.py)'s
  `_write_branch_report` — practice: document-status-header. Re-run clean
  on both checks afterward.
- **The regenerated `record/stale_branches.md` initially failed the leak
  gate**: one line matches an individual-blocklisted term, coming from a
  real, already-pushed branch name (Morgan F, 2026-09-08). The gate did
  its job, flagging it before anything was pushed. Put to the repo owner:
  the term isn't sensitive and the branch doesn't need renaming, so the
  file is committed as generated. CI's own leak gate check only runs the
  structural half here — the vocabulary layer that flagged this reads a
  private blocklist this session's clone of `precedent-individual`
  resolves locally and CI has no access to — so this was a call only a
  person with the private list, or the repo owner directly, could make.
- **Two reader-facing documents were unknown to the currency registry**
  (`documentation/CLOUD_SETUP.md`, `documentation/PER_MACHINE_SETUP.md`),
  so nothing could tell when either went stale. Both added to
  [tools/doc_coverage.json](../tools/doc_coverage.json) with what they
  describe.
- **Base-branch drift: none.** Every commit on `origin/main` has a
  patch-equivalent on `origin/precedent-beta-v01`.
- **Endgame merge rehearsal: 0 conflicts, 0 silent disappearances.**
- **Bootstrap drift, convergent drift, and template freshness gaps in the
  four private sets** are real (23, 4, and 5 findings respectively) and
  stay `HANDOFF` — this session cannot write to any of those repos.
- **This checkout owes verdicts on 8 unlanded branches** (of 13 total
  across every repo in force) the tool's UNLANDED WORK section lists, four
  of them carrying hundreds of commits with no patch-equivalent on
  `precedent-beta-v01`
  (`claude/a-spawned-session-can-answer`, 485; `claude/apply-writes-neither-half`,
  482; `agents-cross-tier-and-git-author-gotchas`, 240;
  `claude/bestpractice-migration-cleanup-i5s118`, 210) — read far enough to
  know whether each is superseded work or something real still waiting,
  and none of that reading happened this run. See
  [record/stale_branches.md](../record/stale_branches.md) for the full
  branch list with delete links, and this run's `--record-pass` entry in
  [record/very-deep-check-ledger.json](../record/very-deep-check-ledger.json)
  for the section-by-section counts.
- **10 branches in this checkout are merged and stale (>= 30 days)** —
  safe deletion candidates once authorship is confirmed against each PR;
  not deleted here.

### Prerequisites

All four sources cloned by the SessionStart hook before the first turn,
all four behind their origin; `precedent_refresh_sources.py --apply`
brought each to the current engine (local only — none of the four private
repos accept a push from this session, confirmed by the tool's own
`git push --dry-run` probe). This checkout was current with
`origin/precedent-beta-v01` at the start.

## Runs so far

| Run | Passes completed | What it changed |
|---|---|---|
| 2026-09-19 | 2 (partial), 4 (partial); 1, 3 not run | On direct request. Mechanical only: `verify_harness.py`, `precedent_check.py`, `doc_lint.py`, `doc_sync.py`, `leak_gate.py`, and the tool's own scans, against the state five days after the last run. One defect fixed: `record/stale_branches.md` (the tool's own pass-4 output) carried no lifecycle frontmatter, failing `document-status-header`. One vocabulary leak-gate hit on an already-pushed branch name, reviewed and accepted by the repo owner (not a CI-visible check — the vocabulary layer needs a private blocklist CI has no access to), so the branch report is committed as generated. Two reader-facing documents added to the currency registry. Base-branch drift none; endgame merge clean. Verdicts not assigned on any of the 238 listed branches, 13 of them carrying real unlanded work (8 in this checkout, four hundreds of commits deep); pass 1 and pass 3 not attempted. |
| 2026-09-14 (evening) | 2 (partial), 3 (partial), 4 (partial); 1 not run | On Morgan's direct request, time-boxed to twenty minutes. Read only what moved since the morning run: the day's three new documents and seven changed install documents, checked link by link and flag by flag against the tree; the tool's own scans. Two defects, both fixed: README.md giving the frozen catalogue as 52 practices where the file says 53, and two new reader-facing documents missing from the currency registry. Base-branch drift none; endgame merge clean; the private sets' bootstrap drift unchanged and still `HANDOFF`. |
| 2026-09-14 | 1 (partial), 2, 3, 4 (partial) | On Morgan's direct request, with the adopter experience as the brief. Four literal rehearsals by sessions with no context — the guided SETUP.md install, a §0 install, a migration, a six-day-old consumer's update — found 65 defects, eight roadblocks; every one fixable from here was fixed the same day (a skeleton slug collision that refused a migration's first sync, an API-budget check firing on every fresh consumer, a template's dead links going red on the adopter's first check, the update leaving every session start warning). The dominant finding is a decision: the guided default installs §1, which turns on none of the loader the pitch describes. Pass 4 found the phase-7 merge into `main` had landed that day unnoticed; its retirement item is now `ask`. Pass 1 partial (no real consumer attached, third run running); the full catalogue read not done. |
| 2026-09-11 | 1 (partial), 2, 3, 4 (partial) | On Morgan's direct request. Every finding one shape: a mechanism changed and the sentences describing it did not. `precedent_sync_views.py` made `--repo` mandatory and seven documented invocations still omitted it — including the one running in every adopter session and the one shipped into every adopter repo. INSTALL.md §2 had no step for a §0 install's practice catalogue, so a consumer taking the documented update kept 72 practices against upstream's 98 and reported `OK`. Two checks that could not pass on a correct fresh install (`github-setup-disclosed`, `acronyms-glossary` — the latter measuring its vocabulary from tracked markdown, so it reported words from the vendored catalogue). One shipped template restating four catalogue rules as its own, one of them resident. And the phase-7 merge, recorded at 0 conflicts, re-rehearsed at 2. Pass 1 partial (no real consumer attached); pass 4's full catalogue read recorded as not done. |
| 2026-09-08 | 1, 2, 3, 4 | Ahead of showing `precedent-beta-v01` to Alex. Six defects, all fixed and pushed: the unlanded-work scan fabricating work on a shallow clone; `seed` and `refresh` between them leaving a renamed-away engine file in every adopter's tree, permanently; the withdrawn-practices table linking a successor that lives in another source, which failed a team set's own light-check; a session whose hooks never ran, so 53 private practices were silently not in force; the checkout being moved off its working branch mid-session (cause NOT found — detector added); and this practice's own pass-3 bullet instructing a session to reverse a decision Morgan made that morning. All three practice sets refreshed onto the current engine and their orphaned file removed. |
| 2026-09-07 | 1, 2, 3, 4 — all four | The first run to complete all four passes under this practice. ≈30 defects found and fixed across four repositories: 6 in pass 1, 8 in pass 2, the rest in passes 3 and 4. Shipped `internal_paths` and `output_paths` for headline scoping, two content-corruption fixes in `title_case.py`, the failure recap in `verify_harness.py`, a hermetic fixture, the merge-commit backstop, commit identity reaching every attached repo, the within-source conflict scan, and `tracked-practice-files`. Promoted `fail-gracefully` and `bold-key-phrases` to universal, ending two same-level collisions. Pass 4's 53 sequential judgments deliberately not run — see the closing note. |

The 2026-09-06 [pre-launch audit](PRELAUNCH_AUDIT.md) is the closest thing to
a prior run, and is where pass 1's method and all but one of pass 2's
questions come from — it was not run under this practice, and its own
still-open list is a separate document, kept there rather than copied here.
