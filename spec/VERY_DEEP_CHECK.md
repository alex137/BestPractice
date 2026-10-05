---
title:         Very deep check — run record
kind:          record
status:        live
opened:        2026-09-19
closed:        null
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
[todo/](../todo/TODO.md) line it went to. When the last pass is done, collapse
the run to one row under "Runs so far" and clear the table for the next one —
this document holds the run in progress, not an archive of every finding
([docs-are-current-state](../practices/docs-are-current-state.md); the
findings themselves live in the commits that fixed them and in
[todo/](../todo/TODO.md)).

## Branches safe to delete right now

**Mechanically proven safe** — every commit on each of these is already an
ancestor of this repo's declared `base_branch` (`staging`) — and stale enough (>= 30 days untouched)
that nobody is likely to still have it checked out. Written directly by
`tools/very_deep_check.py` whenever this checkout's own branch scan runs
(never `doc_sync.py` — this reads the real GitHub origin live, which
`doc_sync.py`'s reproducibility contract does not fit; see the comment
above `PAIRS` in [tools/doc_sync.py](../tools/doc_sync.py)), so it is
current as of the last real scan, not necessarily this instant. Regenerate
on its own with
`python3 tools/very_deep_check.py --emit merged-stale-checkout`. A session
cannot delete a branch (`git push origin --delete` is refused outright,
same wall as
[todo-2026-09-14-branch-merge-or-close-verdicts.md](../todo/todo-2026-09-14-branch-merge-or-close-verdicts.md)),
so this is a page to click through, not a to-do for a session.

<!--vdc-embed:merged-stale-checkout: never hand-edit -- written by
tools/very_deep_check.py's checkout branch scan, not doc_sync.py -->
(none -- no merged branch is >= 30 days stale right now)
<!--/vdc-embed:merged-stale-checkout-->

## Practice catalogue

**Not kept here since 2026-09-28.** Every run hands the person a review
page in the session instead: the branches they can delete, with a link
each, and every active practice by source, private sets included. It is
never committed or linked from a repository, so this public file carries
none of it. How it works: [very-deep-check](../practices/very-deep-check.md)
and `tools/precedent_review_page.py`.

## Current run

**The full account of this run, pass by pass: [VERY_DEEP_CHECK_LATEST_RUN.md](VERY_DEEP_CHECK_LATEST_RUN.md).**

**2026-10-05, on the phrase.** All four passes, across BestPractice, the
individual set and the writing and ladder sets; the two sets folded into
universal that day were read only for their retirement. This session could
push to BestPractice alone. It skipped the full harness and the passes at
first, and did both after Morgan asked.

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | done, gaps named | 2026-10-05 | Four routes rehearsed on `main`; no migration, no practice moves, no real consumer. Two fixed. Unfixed: [todo-2026-10-05-very-deep-check-pass-1-findings](../todo/todo-2026-10-05-very-deep-check-pass-1-findings.md) |
| 2 — mechanisms | done, gaps named | 2026-10-05 | The tool's seven items reproduced; questions 1, 4-12, 16-19, 22, 23 not worked one by one. Three of the check's own sections fixed. Unfixed: [todo-2026-10-05-very-deep-check-pass-2-findings](../todo/todo-2026-10-05-very-deep-check-pass-2-findings.md) |
| 3 — coherence read | done, gaps named | 2026-10-05 | Fold seam swept in every repo; universal swept, not read in full. BestPractice wording fixed. Unfixed: [todo-2026-10-05-very-deep-check-pass-3-findings](../todo/todo-2026-10-05-very-deep-check-pass-3-findings.md) |
| 4 — catalogue, backlog, branches | done | 2026-10-05 | Every branch from full clones, 46 pairs judged, six items closed. Unfixed: [todo-2026-10-05-very-deep-check-pass-4-findings](../todo/todo-2026-10-05-very-deep-check-pass-4-findings.md) |

## Runs so far

| Run | Passes completed | What it changed |
|---|---|---|
| 2026-10-05 | 1, 2, 3, 4 | Described under "Current run" above until the next run replaces it. |
| 2026-09-28 | 1, 2, 3, 4 | All four passes across five repos plus the first real consumer; ten sub-agents; the first full sequential catalogue judgment (216 practices). Findings: `todo-2026-09-28-very-deep-check-pass-{1,2,3,4}-findings`. |
| 2026-09-22 | mechanical only | A tool run with no passes recorded in the ledger and no row here until 2026-09-28; nothing in this file says what, if anything, it read. |
| 2026-09-21 | 1 (partial), 2 (partial), 3, 4 | The full four passes, scope said up front, while two other sessions pushed to the integration branch. Pass 1: five fixtures, one silently destructive defect and a roadblock (no consumer attached). Pass 2: all 69 tools' read-only verbs; 8 of 20 questions not attempted. Pass 3: all five catalogues and 33 shipped templates. Pass 4: verdicts on 11 branches (their counts were inflated by the shallow-fetch defect found 2026-09-28). Fixed in place: a retired `Session Text` command AGENTS.md still advertised against the rule in force, stale `Go merge` triggers, a wrong gotcha count, a quick-index row to a redirect stub. Findings: `todo-2026-09-21-pass-{1,2,3,4}-*`. |
| 2026-09-20 (afternoon) | 1, 2, 3 (targeted); 4 not repeated | On Morgan's direct request, a follow-up to the same-day morning run — flagged before starting, because the actual delta (103 commits, ~7 hours) was far larger than the morning run's own 5-commit precedent for "narrow": README rewrite work, but also real engine changes (`verify_harness.py`, `doc_lint.py`'s new frontmatter-YAML check, `precedent_vendor_engine.py`'s CI-workflow retirement) and a go-update.md rewrite retiring "Go merge" as a trigger. Morgan chose "Targeted": mechanical suite re-run, a real (not full five-path) Pass 1 rehearsal scoped to the changed engine/install files, and a Pass-3 diff read of the 103 commits rather than the full catalogue. Pass 1 (sub-agent): built a scratch consumer pinned at the morning run's commit, refreshed it forward via `precedent_vendor_engine.py refresh`, hand-verified the refresh-replaces-itself self-heal path, ran `verify_harness.py`/`doc_lint.py` directly — clean, no findings. Pass 3 (sub-agent): 5 findings, all fixed same session — go-update's retirement never reached 9 places still teaching "Go merge" as live (the brand-new `prompt-please.md`'s own paste-ready template, 5 `documentation/` surfaces, and `templates/document-project/AGENTS.md`, which vendors the stale phrase into every adopting project), and `spec/README_REWRITE_PROPOSAL.md` still said "Nothing here touches README.md" / `status: drafted` after the rewrite had already landed as README.md and kept moving under 20+ further edits — marked `status: executed`, reworded. Mechanical five-gate suite (`verify_harness`/`doc_lint`/`leak_gate`/`precedent_check`/`doc_sync`) re-run clean after the fixes. Pass 4 not repeated — this morning's per-branch verdicts stand, nothing suggested branches moved. A single further commit (PR #493, a name-boundary fix in `precedent_decommission.py`) landed from elsewhere while this run was in progress; out of scope for this run, left for the next one. Private sets: still `HANDOFF`, unchanged. |
| 2026-09-20 | 1 not run; 2, 3, 4 (partial) | On Morgan's direct request, one day after the 2026-09-19 full run. Scoped narrow up front and said so before running: only 5 commits had landed since 09-19 (2 doc-recipe fixes, 3 `HUMANS_AT_OUR_BEST`/philosophy edits), so this run skipped pass 1's rehearsals and pass 3's full catalogue re-read rather than repeat them a day later. Sources refreshed to current locally (`precedent_refresh_sources.py --apply`); the four private sets still `HANDOFF` (git-proxy access denied, confirmed by `--dry-run` probe) — none of their bootstrap/convergent/template-freshness drift is fixable from here. Mechanical five-gate suite: 1 real finding, `verify_harness.py`'s real-YAML-parser check — 17 `todo/*.md` files (16 found on the first pass, 1 more on a full-tree sweep after the first fix left the check still red) had a `decision:` frontmatter field opening `""` with an unescaped internal quote, which this repo's own permissive reader tolerated and PyYAML rejected; fixed by escaping the embedded quotes, verified clean on both the check and a direct parse. Narrow pass-3 read of the 5 landed commits: a link-text rename (`Our Working Loop` → `The Working Loop`) checked for stale references elsewhere (none) and for broken links via `doc_lint.py` against the 12 changed files explicitly (clean, only pre-existing warning-level unlinked-reference notices unrelated to this change). Unlanded-work inventory and live-session sweep read (not judged): 11 branches across this checkout and 3 private sources carry unlanded work, 14 more unmeasurable from a shallow clone; live-session sweep cross-checked against `list_sessions`/`get_session` found the two other sessions active on this repo since 09-19 (`Humans at our best content edits`, `CI/CD minutes cost escalation`) both completed and pushed, nothing orphaned. Base-branch drift: none. Endgame merge rehearsal: 0 conflicts, 0 silent disappearances (both under the same shallow-clone caveat the tool prints). GitHub API budget: 99.6-99.7% of the core allowance left. Pass 4's real per-branch merge-or-close judgment not repeated (09-19's verdicts stand); pass 1 not run at all. |
| 2026-09-19 | 1, 2, 3, 4 — all four | On direct request; started mechanical-only, corrected mid-run to the full four passes after "the whole point of 'very deep check' is to do a very deep check" — now its own practice correction in `very-deep-check.md`. Pass 1: real install rehearsal, reproduces todo-114. Pass 2: mechanical suite clean. Pass 3: full 130-file catalogue coherence read (sub-agent), 25 findings, 3 categories fixed, rest queued in a new todo item. Pass 4: real per-branch judgment on this checkout's 8 unlanded branches (sub-agent, unshallowed clone, GitHub history checked) found the tool itself was fabricating 210-485 "unlanded commits" on branches already deleted upstream — 2 real bugs fixed (missing `--prune`, an `ahead` count computed before its merge-base precondition), the branch report shrank 617 → 341 lines. `record/stale_branches.md`'s own first commit tripped `filename-separator` (renamed to match `GOTCHAS_ARCHIVE.md`'s underscore) and the individual blocklist's vocabulary layer (accepted by the repo owner, not CI-visible). Base-branch drift none; endgame merge clean; the four private sets' bootstrap/convergent/template-freshness drift unchanged and still `HANDOFF`. Full catalogue's ~53-practice sequential judgment still not done — no run in this ledger ever has. |
| 2026-09-14 (evening) | 2 (partial), 3 (partial), 4 (partial); 1 not run | On Morgan's direct request, time-boxed to twenty minutes. Read only what moved since the morning run: the day's three new documents and seven changed install documents, checked link by link and flag by flag against the tree; the tool's own scans. Two defects, both fixed: README.md giving the frozen catalogue as 52 practices where the file says 53, and two new reader-facing documents missing from the currency registry. Base-branch drift none; endgame merge clean; the private sets' bootstrap drift unchanged and still `HANDOFF`. |
| 2026-09-14 | 1 (partial), 2, 3, 4 (partial) | On Morgan's direct request, with the adopter experience as the brief. Four literal rehearsals by sessions with no context — the guided SETUP.md install, a §0 install, a migration, a six-day-old consumer's update — found 65 defects, eight roadblocks; every one fixable from here was fixed the same day (a skeleton slug collision that refused a migration's first sync, an API-budget check firing on every fresh consumer, a template's dead links going red on the adopter's first check, the update leaving every session start warning). The dominant finding is a decision: the guided default installs §1, which turns on none of the loader the pitch describes. Pass 4 found the phase-7 merge into `main` had landed that day unnoticed; its retirement item is now `ask`. Pass 1 partial (no real consumer attached, third run running); the full catalogue read not done. |
| 2026-09-11 | 1 (partial), 2, 3, 4 (partial) | On Morgan's direct request. Every finding one shape: a mechanism changed and the sentences describing it did not. `precedent_sync_views.py` made `--repo` mandatory and seven documented invocations still omitted it — including the one running in every adopter session and the one shipped into every adopter repo. INSTALL.md §2 had no step for a §0 install's practice catalogue, so a consumer taking the documented update kept 72 practices against upstream's 98 and reported `OK`. Two checks that could not pass on a correct fresh install (`github-setup-disclosed`, `acronyms-glossary` — the latter measuring its vocabulary from tracked markdown, so it reported words from the vendored catalogue). One shipped template restating four catalogue rules as its own, one of them resident. And the phase-7 merge, recorded at 0 conflicts, re-rehearsed at 2. Pass 1 partial (no real consumer attached); pass 4's full catalogue read recorded as not done. |
| 2026-09-08 | 1, 2, 3, 4 | Ahead of showing `precedent-beta-v01` to Alex. Six defects, all fixed and pushed: the unlanded-work scan fabricating work on a shallow clone; `seed` and `refresh` between them leaving a renamed-away engine file in every adopter's tree, permanently; the withdrawn-practices table linking a successor that lives in another source, which failed a team set's own light-check; a session whose hooks never ran, so 53 private practices were silently not in force; the checkout being moved off its working branch mid-session (cause NOT found — detector added); and this practice's own pass-3 bullet instructing a session to reverse a decision Morgan made that morning. All three practice sets refreshed onto the current engine and their orphaned file removed. |
| 2026-09-07 | 1, 2, 3, 4 — all four | The first run to complete all four passes under this practice. ≈30 defects found and fixed across four repositories: 6 in pass 1, 8 in pass 2, the rest in passes 3 and 4. Shipped `internal_paths` and `output_paths` for headline scoping, two content-corruption fixes in `title_case.py`, the failure recap in `verify_harness.py`, a hermetic fixture, the merge-commit backstop, commit identity reaching every attached repo, the within-source conflict scan, and `tracked-practice-files`. Promoted `fail-gracefully` and `bold-key-phrases` to universal, ending two same-level collisions. Pass 4's 53 sequential judgments deliberately not run — see the closing note. |

The 2026-09-06 [pre-launch audit](PRELAUNCH_AUDIT.md) is the closest thing to
a prior run, and is where pass 1's method and all but one of pass 2's
questions come from — it was not run under this practice, and its own
still-open list is a separate document, kept there rather than copied here.
