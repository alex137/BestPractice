---
title:         Very deep check — run record
kind:          record
status:        closed
opened:        2026-09-14
closed:        2026-09-14
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

**Started and finished 2026-09-14, evening**, on Morgan's direct request
("Very deep check again"), **time-boxed by him to twenty minutes**. That
bound is the run's most important fact: it is the second run of the day,
it read only what moved since the morning run closed (PRs #399 through
#402, and the two commits between them), and every pass below is marked
PARTIAL or not run against the practice's full scope. A later session that
wants the full read resumes from the morning run's own "not done" items,
not from here. Scope: this checkout on `precedent-beta-v01`, worked on
`claude/deep-check-fe1t02`; the individual set and the three team sets
were refreshed to the current engine and read by the tool, not written
(every one probes `HANDOFF` from here, and their refreshed working trees
were left for their own sessions to publish).

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | done (PARTIAL) | 2026-09-14 | one rehearsal, in the ten minutes left over: SETUP.md's exact installer command into a scratch project. **Roadblock found**: the adopter's first check reads `3 violated` where the page promises `0`, and its `AGENTS.md` carries three of the operator's private practices — [TODO.md 114](../todo/todo-2026-09-14-installer-inherits-the-operators-individual-set.md), `ask` |
| 2 — mechanisms | done (PARTIAL) | 2026-09-14 | mechanical only: the tool's own sections, `doc_sync`, `precedent_check` (0 violated), `doc_lint` on the touched files; no tool was read against its own description |
| 3 — coherence read | done (PARTIAL) | 2026-09-14 | the day's three new documents and the seven changed install documents, read against the tree by two readers with no other context; one contradiction, fixed |
| 4 — catalogue, backlog, branches | done (PARTIAL) | 2026-09-14 | the tool's branch, base-drift and open-item scans read; the full catalogue read recorded as not done, same reason as the last three runs |

**One roadblock found, in the last ten minutes, and recorded rather than fixed** (TODO.md 114: the installer writes the operator's individual set into the adopter's project). What the run found and did:

- **README.md said the frozen catalogue holds 52 practices; the file it
  links says 53, and has 53 headings.** Fixed in README.md.
- **Two reader-facing documents that landed today were unknown to the
  currency registry** (`documentation/GITHUB_SETTINGS.md`,
  `documentation/TEN_THINGS.md`), so nothing could tell when either went
  stale. Both added to [tools/doc_coverage.json](../tools/doc_coverage.json)
  with what they describe.
- **Every link, anchor, command and flag the day's documents cite exists**
  (the readers checked each one against the tree), and the precedence
  order is stated the same way in the three places it appears.
- **Base-branch drift: none.** Every commit on `origin/main` has a
  patch-equivalent on the branch, on a shallow clone — the caveat the tool
  prints applies.
- **Endgame merge rehearsal: 0 conflicts, 0 silent disappearances.**
- **Bootstrap and convergent drift in the four private sets** is the same
  finding the morning run recorded, now against the refreshed engine; it is
  those repositories' own work and stays `HANDOFF`.
- **Open items naming a file that is gone: 11**, the same list as the
  morning; the tool proposes and does not close, and nothing here was
  closed.
- **Unlanded work: 5 branches**, two in this checkout.
  `open-item-and-gotcha-plan` moved today with four commits and is
  Morgan's; `claude/file-sharing-service-spec-0m9c7p` has three commits
  from July. No verdict given in a time-boxed run; both carried to the next
  full pass 4.
- **`spec/SOURCES.md`'s title still says "Three Sources"** while its body
  documents four. Not a finding: the document says so itself, on purpose,
  as a dated addendum over rewritten history.

### Prerequisites

All four sources cloned by the SessionStart hook before the first turn,
all four behind their origin; `precedent_refresh_sources.py --apply`
brought each to the current engine. This checkout was current with
`origin/precedent-beta-v01` at the start.

## Runs so far

| Run | Passes completed | What it changed |
|---|---|---|
| 2026-09-14 (evening) | 2 (partial), 3 (partial), 4 (partial); 1 not run | On Morgan's direct request, time-boxed to twenty minutes. Read only what moved since the morning run: the day's three new documents and seven changed install documents, checked link by link and flag by flag against the tree; the tool's own scans. Two defects, both fixed: README.md giving the frozen catalogue as 52 practices where the file says 53, and two new reader-facing documents missing from the currency registry. Base-branch drift none; endgame merge clean; the private sets' bootstrap drift unchanged and still `HANDOFF`. |
| 2026-09-14 | 1 (partial), 2, 3, 4 (partial) | On Morgan's direct request, with the adopter experience as the brief. Four literal rehearsals by sessions with no context — the guided SETUP.md install, a §0 install, a migration, a six-day-old consumer's update — found 65 defects, eight roadblocks; every one fixable from here was fixed the same day (a skeleton slug collision that refused a migration's first sync, an API-budget check firing on every fresh consumer, a template's dead links going red on the adopter's first check, the update leaving every session start warning). The dominant finding is a decision: the guided default installs §1, which turns on none of the loader the pitch describes. Pass 4 found the phase-7 merge into `main` had landed that day unnoticed; its retirement item is now `ask`. Pass 1 partial (no real consumer attached, third run running); the full catalogue read not done. |
| 2026-09-11 | 1 (partial), 2, 3, 4 (partial) | On Morgan's direct request. Every finding one shape: a mechanism changed and the sentences describing it did not. `precedent_sync_views.py` made `--repo` mandatory and seven documented invocations still omitted it — including the one running in every adopter session and the one shipped into every adopter repo. INSTALL.md §2 had no step for a §0 install's practice catalogue, so a consumer taking the documented update kept 72 practices against upstream's 98 and reported `OK`. Two checks that could not pass on a correct fresh install (`github-setup-disclosed`, `acronyms-glossary` — the latter measuring its vocabulary from tracked markdown, so it reported words from the vendored catalogue). One shipped template restating four catalogue rules as its own, one of them resident. And the phase-7 merge, recorded at 0 conflicts, re-rehearsed at 2. Pass 1 partial (no real consumer attached); pass 4's full catalogue read recorded as not done. |
| 2026-09-08 | 1, 2, 3, 4 | Ahead of showing `precedent-beta-v01` to Alex. Six defects, all fixed and pushed: the unlanded-work scan fabricating work on a shallow clone; `seed` and `refresh` between them leaving a renamed-away engine file in every adopter's tree, permanently; the withdrawn-practices table linking a successor that lives in another source, which failed a team set's own light-check; a session whose hooks never ran, so 53 private practices were silently not in force; the checkout being moved off its working branch mid-session (cause NOT found — detector added); and this practice's own pass-3 bullet instructing a session to reverse a decision Morgan made that morning. All three practice sets refreshed onto the current engine and their orphaned file removed. |
| 2026-09-07 | 1, 2, 3, 4 — all four | The first run to complete all four passes under this practice. ≈30 defects found and fixed across four repositories: 6 in pass 1, 8 in pass 2, the rest in passes 3 and 4. Shipped `internal_paths` and `output_paths` for headline scoping, two content-corruption fixes in `title_case.py`, the failure recap in `verify_harness.py`, a hermetic fixture, the merge-commit backstop, commit identity reaching every attached repo, the within-source conflict scan, and `tracked-practice-files`. Promoted `fail-gracefully` and `bold-key-phrases` to universal, ending two same-level collisions. Pass 4's 53 sequential judgments deliberately not run — see the closing note. |

The 2026-09-06 [pre-launch audit](PRELAUNCH_AUDIT.md) is the closest thing to
a prior run, and is where pass 1's method and all but one of pass 2's
questions come from — it was not run under this practice, and its own
still-open list is a separate document, kept there rather than copied here.
