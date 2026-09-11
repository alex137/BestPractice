---
title:         Very deep check — run record
kind:          record
status:        closed
opened:        2026-09-06
closed:        2026-09-11
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

**Started 2026-09-11**, on Morgan's direct request ("very deep check").
Scope: every repo in force — `alex137/BestPractice`, the individual set,
and the three team sets (`repo-maintenance`, `writing`, and the
working-style one, which this document deliberately does not name in full;
see below). Worked directly on `precedent-beta-v01` in this checkout; the
source sets were read, not written.

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | done (PARTIAL) | 2026-09-11 | fresh install and, for the first time, a stale consumer brought forward — five defects, the worst of them silent; no real consumer repository was attached, so the step that found seven defects last time did not run |
| 2 — mechanisms | done | 2026-09-11 | the read-only verbs, the unreachable-source path, the duplicate hunt and the inherited-configuration list all came back clean; one finding lands in another owner's repo |
| 3 — coherence read | done | 2026-09-11 | whole-tree lint clean; one shipped template found restating four catalogue rules as its own, one of them resident |
| 4 — catalogue, backlog, branches | done (PARTIAL) | 2026-09-11 | branch verdicts below; the endgame-merge figure this repository relies on turned out to be three days wrong; the full catalogue read is recorded as not done, with the reason |

**No roadblock is open.** Every pass-1 and pass-2 finding fixable from this
repository is fixed and verified by rebuilding the fixture, not by re-reading
the diff.

**What a next run should read first.** The previous run's dominant pattern
was *a guard written for the wrong failure mode*. This run's is one step
earlier and cheaper to look for: **a mechanism changed and the sentences
telling people how to use it did not.** Every pass-1 finding is that shape.
`precedent_sync_views.py` made `--repo` mandatory on 2026-09-10 and seven
documented invocations still omitted it, including the one in
`templates/bootstrap.sh` that runs in every adopter session and the one in
the loader template that ships into every adopter repo. `§2` grew an engine
step and never grew a catalogue step. The phase-7 merge was measured at zero
conflicts and `main` moved the next day. **When you find a change, do not
check that it works — check what still describes it**, and prefer the check
that rebuilds the thing described to the one that reads the description.

### Prerequisites

All four sources cloned by the SessionStart hook before the first turn, from
the environment credential, with no `add_repo` call — the route INSTALL.md §8
documents, working end to end. `precedent_session_check.py`: 9 guarantees in
effect, 1 undetermined (the session-root row, which cannot be answered from a
tool shell and is why the effect checks exist).

The deep check suite was green before the passes began — 177 passed / 0
failed, 43 passed / 0 violated, doc_lint and doc_sync clean, leak gate clean
with one note — and green after them.

**`origin/precedent-beta-v01` moved twice under this run**, from a parallel
session. Caught by the update fixture rather than by any gate: the vendor
tool resolved a remote-tracking ref this checkout had not refreshed since
session start. Fast-forwarded and the reading restarted from there. A very
deep check that takes hours cannot treat its opening freshness proof as
holding for the whole run.

### Pass 1 — adopter installs

**The fresh install now comes back clean** (30 passed, 0 violated), and did
not when the run began. Three defects, all found by building the thing the
documents describe:

- **INSTALL.md §0 step 6 does not work as written.**
  `precedent_sync_views.py` made `--repo` mandatory on 2026-09-10 —
  deliberately, with a good reason in the refusal text — and nothing that
  tells anyone to run it was updated. Seven invocations: the install step
  itself, four in `templates/AGENTS.md.loader.template` (which ships into
  every repo installed since), two in the parallel
  `templates/document-project/` set, and `templates/bootstrap.sh`, where the
  drift warning is `>/dev/null 2>&1`-silenced so it now fires on **every
  session in every adopter repo** and names a fix broken the same way.
- **`github-setup-disclosed` cannot pass on a correct §0 install.** The rule
  wants a newly installed workflow named where its people read.
  `templates/GETTING_STARTED.md` described the check in prose and never said
  `doc-lint.yml`, so §0 installs the workflow and fails the rule in the same
  step.
- **`acronyms-glossary` reports words the adopter did not write.** Its
  word-versus-initialism test is measured from the repo's own corpus, and
  the corpus was built from **tracked** markdown — so a repo that has just
  materialized 97 practice files measures its vocabulary against whatever it
  started with (two files, zero caps tokens), and every shouted English word
  inside the **vendored** catalogue reads as an unglossed acronym. `BEFORE`,
  from `quick-index`'s own Rule, was the first hit. The corpus is now tracked
  files union what is on disk, and below 50 caps tokens both callers say they
  cannot decide rather than falling back to the behaviour the measurement was
  built to replace. `templates/TODO.md.template`'s `NAME, YYYY-MM-DD`
  placeholder was a second, smaller instance and is now a worked example.

**The update is where the worse shape was, because it was silent.** Built
for the first time as a real fixture: a consumer vendored at a 2026-09-07
commit, walked through §2 exactly as written.

- **§2 has no step for a §0 install's practice catalogue.** Steps 1–5 are
  §1's `process/upstream/` bookkeeping; step 6 is the engine. Nothing,
  anywhere, updates the vendored `practices/` tree — which is the thing §0
  exists to deliver. The fixture refreshed its tools, reported `OK` from
  every check, and went on materializing **72 practices against upstream's
  98**. §2 now opens with a step 0 for it.
- **The removal guard's refusal named a remedy a §0 repo cannot run.**
  Replacing the catalogue legitimately removes practices retired upstream;
  the guard correctly refuses, and then said to run
  `process/upstream/tools/checkin.py update`, which a §0 install has no
  `process/upstream/` for. It now names both causes and says
  `--allow-removals` is the answer for a real retirement rather than a
  workaround.

The updated consumer comes back clean afterwards (26 passed, 0 violated).

**One documented failure reproduced exactly, which is the good outcome.**
`refresh` on a consumer vendored before 2026-09-08 dies on
`has no tools/precedent_retire_path.py`. INSTALL.md §2 step 6 predicts it,
names the one manual reseed that escapes it, and the escape works. Recorded
here so the next run does not re-file it as a finding.

**PARTIAL, for the same reason as 2026-09-07: no real consumer repository
was attached.** The ask belongs at the top of the run and this session never
made it, which is the failure the order of operations puts it there to
prevent. The scratch fixtures are clean rooms; the last time a real repo was
attached it produced seven defects the fixtures could not.

**BOOTSTRAP DRIFT: 12 findings, none fixable from here.** Every one of the
four sets carries an older vendoring of the engine and a
`freshness-guard.sh` that differs from what the generator writes today. Both
land in repositories under another owner. `precedent_vendor_engine.py refresh`
is the whole fix for the first; the second is TODO's `source-hook-drift`,
now confirmed by a second independent mechanism. **And the individual set's
own `precedent/engine-refresh-c6c885033a9f` branch is an unlanded attempt at
exactly this** — pinned at a commit that is itself now days stale, which is
why the previous run's verdict on it (CLOSE) still stands.

### Pass 2 — mechanisms

Worked the questions that have found something before, and one that had not:

- **Does anything named `--check` write?** Snapshot and diff across all five
  gates: nothing written. Then the harder half — the same `--check` with a
  source unreachable, which once deleted 57 tracked files while printing a
  verdict. It refuses, names the reason, and writes nothing. Tested against a
  throwaway clone rather than this tree, because the failure being tested for
  is a tree-destroying one.
- **Are there two of anything that should be one?** No cross-file duplicate
  function body anywhere in `tools/`. Three `_default_branch()`
  implementations exist and all three consult the declared branch first, which
  is the property the rule is about; they differ only in a documented
  fallback. The duplicate this practice's own Story names — its checklist
  living both here and as a string literal in the tool — is fixed and the tool
  reads the practice file.
- **What does a session inherit that a person configured by hand?** Nine of
  ten guarantees in effect, all from hooks or the environment.
- **Do string matches respect name boundaries?** One finding, and the leak
  gate reports it on every clean run: the private blocklist has no stem for
  `precedent-team-working-style`, so the bare repository name — the form that
  actually reaches a public tree, through a branch or a directory named after
  the repo — matches nothing. The qualified form is refused; the short one is
  not. The set was created after the stems were measured and nothing revisits
  the list when a source is added. **And the gap is wider than a stem: the
  set has no `visibility-audit: allow` line either**, which this run proved
  by tripping it — the first draft of this document named the repository in
  its scope line and the leak gate refused the push, correctly. So the
  qualified form is unnameable here and the bare form is unguarded, which is
  the worst of both. Recorded in
  [TODO.md](../TODO.md#blocklist-stem-team-working-style); the file is in
  another owner's repository.

### Pass 3 — coherence read

**Whole-tree lint clean**: no broken relative link, no accidental
strikethrough rendering as `<del>`, no skipped heading level.

**Rules we ship somewhere else — one finding, and it is the shape this
bullet exists for.** `templates/document-project/AGENTS.md` restated
`section-order-by-frequency`, `doc-references-are-links`,
`readers-vocabulary` and `reply-links-files` in its own words and named none
of them, while every sibling template cites the slug for each.
`reply-links-files` is **resident**, so an adopter instantiating that template
held a paraphrase of it beside the live copy in the generated block, every
turn, with nothing comparing the two — the same construction that put "no
bold inside paragraphs" next to `bold-key-phrases` for weeks. Each bullet now
points at the practice instead of restating it.

**Session load: 26,569 tokens across every repo in force**, of which this
checkout is 21,953 and `AGENTS.md`'s gotchas section alone is 9,231. Every
declared ceiling passes. The three entries the tool flagged as marking their
own trap settled were read against the tree and **all three stay**: the
branch-switch entry says outright that its cause is *not* known and detection
is the whole remedy; the individual-source-clone entry describes a
per-container condition that a current clone today does not disprove (its own
text says to run the command rather than trust a recorded path); and the
third is a policy sentence in "Working in this repo", not a gotcha — a false
positive of the marker heuristic.

**Tier placement: no change.** All ten resident practices are
every-session-always on their occasions. Six carry no `checked_by`, and that
is the right answer rather than a gap: they are judgments about prose and
about when to stop, and the two the loader measurement once caught this way
(`verify-postcondition`, `environment-gotchas`) already have checks.

**Documentation currency: the seven `REVIEW` prompts were read and none was
a finding.** The mover behind most of them was today's rename of the team
source, and the rename commit swept 149 references. What survives of the
older `precedent-team-tms` name is a *different, retired* set named inside
dated records, which is correct history and must not be rewritten. Two
findings the tool raised mechanically are fixed: `Brainstorm` was missing
from the page that teaches the command vocabulary, and
`documentation/INSTALL.md` was reader-facing and unregistered, so nothing
could tell whether it had gone stale.

### Pass 4 — catalogue, backlog, and branches

**The endgame-merge figure this repository relies on is wrong, and had been
for three days.** [TODO.md](../TODO.md) records the phase-7 merge — branch
off `main`, revert the revert, merge — measured 2026-09-07 at **0 conflicts
and a byte-identical tree**. Re-rehearsed whole-tree today with the same
three commands: **2 conflicts**, in `tools/doc_lint.py` and
`tools/model_audit.py`. Both are real work on both sides of the same
function — `main` has an anchor-lint check this branch lacks, this branch has
broken-link and heading-skip checks `main` lacks — so the resolution is a
union and both must survive. The cause is the 2026-09-08 carry onto `main`,
the day after the measurement. **A measured number about two moving branches
is true on the day it was measured and nothing re-runs it**; the item now
says to re-rehearse whenever `precedent_upstream_check.py` reports `main` has
moved, which is printed at every session start and is the trigger the
measurement never had.

The tool's own `ENDGAME MERGE` section reports 504 silently-dropped paths.
That is the same standing condition TODO already documents at 507, with the
safe merge measured — not a new finding.

**Branch verdicts.**

- `alex137/BestPractice: claude/sync-practices-54-55-x2w4n3` — **CLOSE.**
  Reported as carrying 2 unlanded commits, and it carries none: its tip is
  `7d8f5a6`, already on `main`, and `git cherry` calls it unique only because
  it compares against `precedent-beta-v01`. Its diff against this branch
  deletes 28,119 lines because it forked before the restructuring. It is also
  the direct cause of the two phase-7 conflicts above.
- `alex137/BestPractice: claude/file-sharing-service-spec-0m9c7p` — 3
  commits, last moved 2026-07-26, a `share/` spec existing nowhere on this
  branch. **Unchanged from the previous run's verdict: it reads as
  superseded, and it is Alex's repository and his call.** Raise it with him.
  Two runs have now recorded the same recommendation without it being put to
  him, which is itself the drift.
- `alex137/BestPractice: philosophy-bidirectional-slugs` — 2 commits, last
  moved **today**, adding `tools/philosophy_backlinks.py` and bidirectional
  cross-references across `philosophy/`. **Live work from a parallel session;
  no verdict is owed yet.** Re-check next run.
- `themorgan/precedent-individual: precedent/engine-refresh-c6c885033a9f` —
  **CLOSE**, as the previous run already decided. It pins a commit that is now
  days stale, so merging it would refresh that set's engine to something
  already superseded. The verdict was recorded 2026-09-08 and not executed;
  it needs a session rooted in that set.
- **Merged and not deleted**: 6 branches in this checkout are merged and more
  than 30 days finished, and 60-odd more are merged within the window. Every
  one is safe by the ancestor test. The deletions are a GitHub-side chore, not
  a repository change, and are left to a session that can act on them.

**The full catalogue read is recorded as NOT DONE, with the reason.**
`full_practice_audit.py` was run and prints all 141 practices across the five
sources for sequential judgment. That is the whole of its own on-request
practice and more than remained in this session after four passes. Reporting
it as done on a skim is the exact failure `full-practice-audit` was written to
prevent. The previous run recorded the same thing for the same reason.

**The private sets' own backlogs were not swept**, same reason as the
previous run: triaging another person's backlog is not a review's job, and
this session cannot land in those repositories.

## What Each Part of the Check Returned, and What It Cost

Every run appends itself to
[../record/very-deep-check-ledger.json](../record/very-deep-check-ledger.json)
— one row per section: what it found, what it printed (in tokens, the same
words × 1.3 estimate used everywhere else here), and how long it took — and
prints the cross-run read at the end of the run. **Never hand-edit it**: it
is written by
[../tools/very_deep_check.py](../tools/very_deep_check.py), and a figure
typed into it by hand is a figure nothing measured.

**Record each pass here as you finish it, and in the ledger**:

```
python3 tools/very_deep_check.py --record-pass '1=done,findings=2,tokens=140000,note=…'
```

The passes are where this check spends most of what it costs, and no tool
can measure them — so an absent figure is recorded as absent rather than
estimated.

**The answers to what the ledger names as quiet go below, in this table**,
in the run that named them. Three answers, none automatic: **keep** (say
why), **cheapen** (same check, less printed), **retire** (the practice's
Detail loses the bullet, and
[decommission-deletes-files](../practices/decommission-deletes-files.md)
applies to whatever it owned).

| Section | Run that asked | Answer | Why |
|---|---|---|---|
| MACHINE-READABLE FILES | 2026-09-11 | **keep** | ≈20 tokens a run, and it is the one thing here a third-party parser decides rather than this repo's own reader — which is precisely why it once found 14 files the in-house reader was happy with. Cheaper than any answer that changes it. |
| FRESHNESS — declared sources | 2026-09-11 | **keep** | Quiet because it is working. It is the prerequisite the whole check rests on, and this run is the reason to keep it: `origin/precedent-beta-v01` moved twice mid-run, and a source drifting the same way would have inverted every reading below it. |
| REPOS IN FORCE — still there, still writable | 2026-09-11 | **keep** | The newest section here, added 2026-09-11 on Morgan's decision, and three empty runs is not evidence about a guard that young. It also answers the one question nothing else can: an archived repository fetches exactly like a live one and refuses every push. |
| WITHIN-SOURCE CONFLICTS | 2026-09-11 | **keep** | ≈35 tokens, and its silence is load-bearing: the 2026-09-07 run *did* end two same-level collisions by promoting `fail-gracefully` and `bold-key-phrases`, and this is what says none has come back. |
| SOURCE SHAPE | 2026-09-11 | **keep** | ≈26 tokens. It reports `complete` for four sets today and the open TODO item about two sets missing skeleton files is what it found when it was not quiet. |
| ORPHANS | 2026-09-11 | **keep** | ≈44 tokens, and the failure it covers — a renamed-away engine file left in every adopter's tree — is one the 2026-09-08 run actually hit. |
| REPOSITORY VISIBILITY | 2026-09-11 | **cheapen** | The only expensive quiet section: ≈1,738 tokens, 10% of the run's output, and 26 of its 28 lines this run were the identical "GitHub access to this repository is not enabled for this session" sentence repeated per repository. The check is worth keeping — a private repository name reaching a public tree is the failure it exists for — but a session does not need that sentence 26 times. Collapse the unreachable ones to one line with a count and the names, and print the full paragraph only for a repository whose visibility was actually determined. |

## Runs so far

| Run | Passes completed | What it changed |
|---|---|---|
| 2026-09-11 | 1 (partial), 2, 3, 4 (partial) | On Morgan's direct request. Every finding one shape: a mechanism changed and the sentences describing it did not. `precedent_sync_views.py` made `--repo` mandatory and seven documented invocations still omitted it — including the one running in every adopter session and the one shipped into every adopter repo. INSTALL.md §2 had no step for a §0 install's practice catalogue, so a consumer taking the documented update kept 72 practices against upstream's 98 and reported `OK`. Two checks that could not pass on a correct fresh install (`github-setup-disclosed`, `acronyms-glossary` — the latter measuring its vocabulary from tracked markdown, so it reported words from the vendored catalogue). One shipped template restating four catalogue rules as its own, one of them resident. And the phase-7 merge, recorded at 0 conflicts, re-rehearsed at 2. Pass 1 partial (no real consumer attached); pass 4's full catalogue read recorded as not done. |
| 2026-09-08 | 1, 2, 3, 4 | Ahead of showing `precedent-beta-v01` to Alex. Six defects, all fixed and pushed: the unlanded-work scan fabricating work on a shallow clone; `seed` and `refresh` between them leaving a renamed-away engine file in every adopter's tree, permanently; the withdrawn-practices table linking a successor that lives in another source, which failed a team set's own light-check; a session whose hooks never ran, so 53 private practices were silently not in force; the checkout being moved off its working branch mid-session (cause NOT found — detector added); and this practice's own pass-3 bullet instructing a session to reverse a decision Morgan made that morning. All three practice sets refreshed onto the current engine and their orphaned file removed. |
| 2026-09-07 | 1, 2, 3, 4 — all four | The first run to complete all four passes under this practice. ≈30 defects found and fixed across four repositories: 6 in pass 1, 8 in pass 2, the rest in passes 3 and 4. Shipped `internal_paths` and `output_paths` for headline scoping, two content-corruption fixes in `title_case.py`, the failure recap in `verify_harness.py`, a hermetic fixture, the merge-commit backstop, commit identity reaching every attached repo, the within-source conflict scan, and `tracked-practice-files`. Promoted `fail-gracefully` and `bold-key-phrases` to universal, ending two same-level collisions. Pass 4's 53 sequential judgments deliberately not run — see the closing note. |

The 2026-09-06 [pre-launch audit](PRELAUNCH_AUDIT.md) is the closest thing to
a prior run, and is where pass 1's method and all but one of pass 2's
questions come from — it was not run under this practice, and its own
still-open list is a separate document, kept there rather than copied here.
