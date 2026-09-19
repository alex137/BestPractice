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

**Started 2026-09-19 as a mechanical-only pass, corrected mid-run to the
full four passes on direct instruction, and finished the same day.** The
first half ran only the mechanical layer of passes 2 and 4 (the tool's own
scans, `verify_harness.py`/`precedent_check.py`/`doc_lint.py`/`doc_sync.py`/`leak_gate.py`)
and reported passes 1 and 3 as not run, without saying so before
starting. Corrected directly: *"the whole point of 'very deep check' is
to do a very deep check. If I wanted a light check, I wouldn't ask for a
very deep check!"* — recorded as its own practice correction in
[practices/very-deep-check.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/very-deep-check.md)'s
Story. The rest of the run below is the real depth that followed. Scope:
this checkout on `precedent-beta-v01`, worked on
`claude/charming-babbage-ypapbx`; the individual set and the three team
sets were refreshed to the current engine and read by the tool, not
written (every one probes `HANDOFF` from here — this session holds no
credential for `themorgan/precedent-individual` or any
`themorgan/precedent-team-*` repo — and their refreshed working trees were
left for their own sessions to publish).

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | done | 2026-09-19 | real rehearsal: `precedent_install.py` into a fresh scratch project, committed, `precedent_check.py --full-sweep` run against it. Reproduces todo-114 (2 of 3 named checks still violate — the installer still writes the operator's own identity and hooks into a project that never declared them); confirmed the third named check was never a distinct bug, only an artifact of not yet having committed |
| 2 — mechanisms | done | 2026-09-19 | mechanical: `verify_harness.py`, `precedent_check.py`, `doc_lint.py`, `doc_sync.py`, `leak_gate.py`, the tool's own sections; tools not read against their own descriptions |
| 3 — coherence read | done | 2026-09-19 | full 130-file practice catalogue read by a dedicated sub-agent (contradictions, staleness, disproportion, formatting drift, self-application gaps, duplication). 25 findings; 3 small categories fixed in this pass, the rest queued in [todo-2026-09-19-pass-3-coherence-read-findings.md](../todo/todo-2026-09-19-pass-3-coherence-read-findings.md) for the repo owner |
| 4 — catalogue, backlog, branches | done | 2026-09-19 | real judgment on this checkout's 8 unlanded branches by a dedicated sub-agent, on a fully-unshallowed clone, with PR/issue history checked via the GitHub API; found and fixed 2 real bugs in the scan tool itself. Full catalogue read (the ~53-practice sequential judgment) still not attempted — no run in this ledger has ever completed it |

**What the run found and did, roughly in the order it was found:**

- **`record/stale_branches.md` (pass 4's own generated branch report)
  carried no lifecycle frontmatter**, failing `document-status-header` in
  both `precedent_check.py` and `verify_harness.py`. Fixed in
  [tools/very_deep_check.py](../tools/very_deep_check.py)'s
  `_write_branch_report` — practice: document-status-header.
- **Committing that file the first time it ever existed also tripped
  `filename-separator`**: `record/` already carries `GOTCHAS_ARCHIVE.md`
  (underscore), and the report's hyphenated default name was the first
  hyphenated `*.md` there. Renamed to `stale_branches.md` at the source.
- **Regenerating it also matches the individual blocklist's vocabulary
  layer**, on a real, already-pushed branch name. Reviewed with the repo
  owner: the term isn't sensitive, so the file is committed as
  generated — CI's leak gate only runs the structural half here, since
  the vocabulary layer needs a private blocklist CI cannot reach.
- **Two reader-facing documents were unknown to the currency registry**
  (`documentation/CLOUD_SETUP.md`, `documentation/PER_MACHINE_SETUP.md`).
  Both added to [tools/doc_coverage.json](../tools/doc_coverage.json).
- **Pass 1 reproduced todo-114** (installer inherits the operator's
  individual identity and hooks) exactly as the 2026-09-14 run found it;
  confirmed still open, still blocked on the repo owner's call, noted in
  the item rather than re-filed.
- **Pass 3's full catalogue read** found 25 coherence issues across the
  130-file practice catalogue; the small mechanical ones (13 stale
  `spawn-session` link labels left over from its rename to `session-text`,
  5 stray `~` that should read `≈`, 2 unexpanded `VCS` first-uses) were
  fixed in this pass. The larger ones — contradictions around whether
  `create_session`/waking a session is actually retired, `very-deep-check.md`
  and its `approved_by` field's own size (≈19,225 and ≈3,449 words), 39
  practices with no real `## Detail`, a handful of overlapping-occasion
  clusters — are the repo owner's calls, queued in
  [todo-2026-09-19-pass-3-coherence-read-findings.md](../todo/todo-2026-09-19-pass-3-coherence-read-findings.md).
- **Pass 4 found the branch counts this check has been reporting were
  largely fiction.** Four branches long reported as carrying 210-485
  unlanded commits (`agents-cross-tier-and-git-author-gotchas`,
  `claude/a-spawned-session-can-answer`, `claude/apply-writes-neither-half`,
  `claude/bestpractice-migration-cleanup-i5s118`) are plain, fully-landed
  ancestors of both `precedent-beta-v01` and `main`, **already deleted
  from the remote** — the false counts came from two compounding bugs:
  `_fetch_all_heads` never pruned local refs for branches already deleted
  upstream, and `_unmerged_row` computed its `ahead` count before
  confirming the merge-base actually resolved rather than at a shallow
  clone's boundary. Both fixed in
  [tools/very_deep_check.py](../tools/very_deep_check.py) the same run;
  regenerating the branch report afterward dropped it from 617 to 341
  lines. The same bug had put a stale "41 commits" figure into
  [issue #394](https://github.com/alex137/BestPractice/issues/394)
  (`claude/file-sharing-service-spec-0m9c7p`); corrected there to the
  real 3, with a compile-time note that the merge stays clean except one
  `AGENTS.md` row that now belongs in `WHERE_THINGS_ARE.md`.
- **Two branches got real, human-quality verdicts rather than a bare
  count:** `claude/bootstrap-drift-pycache-exclusion-kgtw57` — a traced
  root-cause fix for a bug `PR #427` explicitly deferred, half already
  landed independently, MERGE after a small rebase; and
  `claude/harness-clone-count-1i9qoq` — a self-contained drafted proposal
  document, MERGE (landing a `status: drafted` document is not
  authorizing its implementation, matching this repo's own convention for
  proposals in `spec/`). Neither was merged by this session — merging
  someone else's un-reviewed abandoned work is bigger than what this pass
  does on its own — both are recorded in
  [todo-2026-09-14-branch-merge-or-close-verdicts.md](../todo/todo-2026-09-14-branch-merge-or-close-verdicts.md)
  for a decision.
- `claude/team-sets-carry-code-x2w4n3` — **CLOSE**, added to the same
  item: its proposal was explicitly superseded and closed in PR #444,
  and the superseding PR #455 is merged.
- **Base-branch drift: none.** Every commit on `origin/main` has a
  patch-equivalent on `origin/precedent-beta-v01`.
- **Endgame merge rehearsal: 0 conflicts, 0 silent disappearances.**
- **Bootstrap drift, convergent drift, and template freshness gaps in the
  four private sets** are real (23, 4, and 5 findings respectively) and
  stay `HANDOFF` — this session cannot write to any of those repos.
- **10 branches in this checkout are merged and stale (>= 30 days)** —
  safe deletion candidates once authorship is confirmed against each PR;
  not deleted here.
- **Four branch deletions are now blocked on Morgan alone**
  (`philosophy-bidirectional-slugs`, `claude/sync-practices-54-55-x2w4n3`,
  `precedent/engine-refresh-c6c885033a9f`, and
  `claude/team-sets-carry-code-x2w4n3`, added this run) — `git push
  origin --delete` is refused to a session outright; see
  [todo-2026-09-14-branch-merge-or-close-verdicts.md](../todo/todo-2026-09-14-branch-merge-or-close-verdicts.md).

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
