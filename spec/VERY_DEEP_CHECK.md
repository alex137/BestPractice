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

## Branches safe to delete right now

**Mechanically proven safe** — every commit on each of these is already an
ancestor of `precedent-beta-v01` — and stale enough (>= 30 days untouched)
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

## Current run

**2026-09-21, on the phrase, and committed to the full four passes before
anything ran.** Scope said out loud up front, as the practice requires: this
checkout, the three shared sets, the individual set and `local/` — not the
mechanical half.

**Two other sessions were pushing to `precedent-beta-v01` throughout**
(`Deep check improvements`, which owns `tools/very_deep_check.py` and
`practices/very-deep-check.md` right now, and `Branch deletion practices`).
The checkout went stale under this run three times and was fast-forwarded
each time; step 1's own warning about a stale `AGENTS.md` in context fired
for real, and two of the four pass agents reported it independently.
**Nothing this run found in those two files was edited** — filed instead,
with the one-line fix stated.

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | partial | 2026-09-21 | Five real fixtures built in scratch. One silently destructive defect, one roadblock, nine more. PARTIAL on its own terms: no consumer repository attached, so the pass's highest-yield item was not done. [todo-2026-09-21-pass-1-install-and-update-findings](../todo/todo-2026-09-21-pass-1-install-and-update-findings.md) |
| 2 — mechanisms | partial | 2026-09-21 | Mechanical layer complete and green (see below). The read-the-tools-against-their-own-descriptions half was delegated and had not reported when this record was written; what the parent session found itself is filed as [todo-2026-09-21-template-freshness-reports-five-phantom-gaps](../todo/todo-2026-09-21-template-freshness-reports-five-phantom-gaps.md) and [todo-2026-09-21-deep-check-definition-omits-the-ci-shards](../todo/todo-2026-09-21-deep-check-definition-omits-the-ci-shards.md) |
| 3 — coherence read | done | 2026-09-21 | All five catalogues in force plus the 33 shipped template files. Small findings fixed in the pass; the rest in [todo-2026-09-21-pass-3-coherence-read-findings](../todo/todo-2026-09-21-pass-3-coherence-read-findings.md) |
| 4 — catalogue, backlog, branches | done | 2026-09-21 | Real verdicts on all 11 unlanded branches, every count re-derived from the diff. Backlog and catalogue read. [todo-2026-09-21-pass-4-branch-verdicts-and-catalogue](../todo/todo-2026-09-21-pass-4-branch-verdicts-and-catalogue.md) |

**The starting line had to be earned.** Step 2 wants `0 failed` and
`0 violated` before a line is read, and the tree gave neither: one root
cause — a `command:` field on a private practice that the vocabulary
emitter correctly rendered into a public tracked document — took out
`doc_sync.py`, `precedent_check.py`, and through it the baseline case of
`verify_harness.py --all`. The fix had already landed on the individual
source's `origin/main` (commit `09190a7`) and the local clone was one
commit behind it. Merging that in cleared all three.

**Then both CI shards, which the deep check's own definition does not ask
for.** `INCIDENT COVERAGE`'s standing question — what prevents a
recurrence, and is there a planted case? — answered "nothing" for
`gotcha-2026-09-21-a-green-local-verify-harness-run-does-not-mean-green-ci`.
That gotcha records a session running the full deep check, seeing
`244 passed, 0 failed`, and watching both sharded CI jobs die before
printing a verdict. This run ran them: `243 passed, 0 failed` and
`3 passed, 0 failed`, both green. The gap between what AGENTS.md calls a
deep check and what CI actually runs is filed.

**What this run fixed in place**

- **`AGENTS.md` advertised a retired command that contradicted the rule in
  force.** The `Session Text` bullet outlived `session-text`
  (`status: deduplicated`, superseded by `prompt-please`, absent from the
  18-command vocabulary) and pointed the opposite way on two things:
  *"wake a live session"* against prompt-please's *"never wake a live
  session either"*, and *"the text you hand him carries the merge
  authorization"* against prompt-please's *"only when the person gave one
  for this handoff"*. Every session here read both, on turn one.
- Two surviving `Go merge` trigger references (`AGENTS.md`,
  `three-things.md`) the 2026-09-20 sweep missed while fixing nine.
- A gotcha count in `AGENTS.md` wrong by any reading (said 52; 93 files,
  35 retired, 58 live) — dropped rather than corrected, per
  `no-stale-counts`.
- The quick-index row every session is told to check **first** pointed at
  root `TODO.md`, a redirect stub since 2026-09-16, on a page that also
  says a PR touching that file is refused by CI. Both copies repointed.
- `templates/document-project/AGENTS.md` told adopters to attach every
  `precedent-team-*` source — a glob the 2026-09-18 rename left matching
  nothing, three lines above the rule saying never to hard-code set names.
- 25 bare in-repo references linked; a whole-file read of `AGENTS.md`
  registered against `ACCRETION`'s standing ask.

**What this run filed rather than fixed, and why**

Seven items. Three because the fix lives in a repository this session
cannot reach (`themorgan/precedent-individual`, `themorgan/precedent-shared-*`
— the git proxy refuses across owners, confirmed by a real
`push --dry-run`). Two because the file is owned by a session editing it
right now. Two because they are governance calls rather than a pass's own
tidy-up.

The three worth naming here:

- **`push-back` and `small-calls` are `status: active` at two levels each**,
  with byte-identical bodies, each carrying an `approved_by` saying it was
  moved up from a shared set. Only half of each move happened. Shared beats
  universal, so **the copy that resolves is the old one** and the universal
  copy the occasion index advertises never wins anywhere.
- **`very-deep-check` and `full-practice-audit` carry `scope: null`**,
  which is not one of the two legal values, so both fall through to
  `any-adopter` and ship into every consuming repo. `very-deep-check.md` is
  25,208 words. `spec/PRACTICE_FORMAT.md` names all four as `engine-dev`
  and also says nothing validates the field — a `checkable-gets-checked`
  gap that has now bitten.
- **A consumer's own `AGENTS.md` carries a regenerate command that destroys
  that consumer's `MAP.md` and `GLOSSARY.md`**, replacing them with
  Precedent's own. `orientation-map` is resident, so the map every session
  reads becomes the wrong repository's.

**Expiring practices.** `merge-target-is-beta-branch` is **still binding**.
Its condition is Morgan or Alex saying work moves to `main`, explicitly
*not* a merge into `main` — and `main` took a regular fold-in today
(PR #532). Nobody has said it.

**Container state, both rows red on every session here.** Three shared sets
are cloned twice on this disk, and the session check's stated remedy
(repoint the user config) does not reach them because no config names the
stray path. The beta-branch watermark commits into the individual source
and pushes; from a session rooted here that push cannot land, so every
session leaves another commit — four when this run started, five by the
time it was written up. Both filed.

## Runs so far

| Run | Passes completed | What it changed |
|---|---|---|
| 2026-09-20 (afternoon) | 1, 2, 3 (targeted); 4 not repeated | On Morgan's direct request, a follow-up to the same-day morning run — flagged before starting, because the actual delta (103 commits, ~7 hours) was far larger than the morning run's own 5-commit precedent for "narrow": README rewrite work, but also real engine changes (`verify_harness.py`, `doc_lint.py`'s new frontmatter-YAML check, `precedent_vendor_engine.py`'s CI-workflow retirement) and a go-merge.md rewrite retiring "Go merge" as a trigger. Morgan chose "Targeted": mechanical suite re-run, a real (not full five-path) Pass 1 rehearsal scoped to the changed engine/install files, and a Pass-3 diff read of the 103 commits rather than the full catalogue. Pass 1 (sub-agent): built a scratch consumer pinned at the morning run's commit, refreshed it forward via `precedent_vendor_engine.py refresh`, hand-verified the refresh-replaces-itself self-heal path, ran `verify_harness.py`/`doc_lint.py` directly — clean, no findings. Pass 3 (sub-agent): 5 findings, all fixed same session — go-merge's retirement never reached 9 places still teaching "Go merge" as live (the brand-new `prompt-please.md`'s own paste-ready template, 5 `documentation/` surfaces, and `templates/document-project/AGENTS.md`, which vendors the stale phrase into every adopting project), and `spec/README_REWRITE_PROPOSAL.md` still said "Nothing here touches README.md" / `status: drafted` after the rewrite had already landed as README.md and kept moving under 20+ further edits — marked `status: executed`, reworded. Mechanical five-gate suite (`verify_harness`/`doc_lint`/`leak_gate`/`precedent_check`/`doc_sync`) re-run clean after the fixes. Pass 4 not repeated — this morning's per-branch verdicts stand, nothing suggested branches moved. A single further commit (PR #493, a name-boundary fix in `precedent_decommission.py`) landed from elsewhere while this run was in progress; out of scope for this run, left for the next one. Private sets: still `HANDOFF`, unchanged. |
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
