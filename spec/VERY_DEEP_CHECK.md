---
title:         Very deep check — run record
kind:          record
status:        closed
opened:        2026-09-06
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

**Started and finished 2026-09-14**, on Morgan's direct request ("very deep
check", with a specific ask: the install and migration experience for a
technical and a non-technical adopter, and the things nobody thought to
check). Scope: every repo in force — `alex137/BestPractice`, the individual
set and the three team sets — plus three scratch adopters built for the
run. Worked on `precedent-beta-v01` in this checkout; the four source sets
were read, not written (every one probes `HANDOFF` from here).

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | done (PARTIAL) | 2026-09-14 | four rehearsals, each with fresh eyes: the guided SETUP.md install, a §0 install, a migration, and a six-day-old consumer's update — 65 findings between them, eight of them roadblocks; no real consumer attached, so PARTIAL for the third run running |
| 2 — mechanisms | done | 2026-09-14 | two tools defining "a command" differently, the private practices unreachable by the command that tells a session to read them, the check's own 10,000-token reprint, and a session-start misdiagnosis recorded |
| 3 — coherence read | done | 2026-09-14 | the install documents contradicting themselves and each other; a template telling the installer to ask what the runbook says never to ask; numbered citations into a frozen catalogue |
| 4 — catalogue, backlog, branches | done (PARTIAL) | 2026-09-14 | **the phase-7 merge into `main` landed today and nothing here had noticed**; branch verdicts; the full catalogue read recorded as not done, same reason as before |

**No roadblock is open that this repository can close.** Every pass-1
roadblock fixable from here is fixed and re-verified by rebuilding the
fixture. Two are decisions and are recorded as `ask`
([TODO.md's `setup-default-is-the-loader`](../TODO.md#setup-default-is-the-loader)
and [`retire-merge-target-practice`](../TODO.md#retire-merge-target-practice)).

**What a next run should read first.** The last run's pattern was *a
mechanism changed and the sentences describing it did not*. This run's is
one layer out: **the documents describe a system, and the default path
installs a different one.** A non-technical administrator who reads
[documentation/ADOPTING.md](../documentation/ADOPTING.md) ("they show up when
they matter"; "where a practice can be checked, it is") and then pastes
[SETUP.md](../SETUP.md) gets INSTALL.md §1 — the classic vendored prose,
with no resident block, no occasion index and no enforced check, because
[templates/AGENTS.md.template](../templates/AGENTS.md.template) carries no
generated block and §1 never runs the sync. Nothing was wrong with any one
sentence; the pitch, the guided install and the loader had simply never
been put in front of the same reader at once. **When you rehearse an install,
rehearse it as the person the document is written for, and then ask whether
what landed is what the pitch promised.**

### Prerequisites

All four sources cloned by the SessionStart hook before the first turn.
`precedent_session_check.py`: 9 guarantees in effect, 2 undetermined.

**The first tool call of the session was refused by the freshness guard**,
which reported the checkout *diverged* (132 local, 219 remote) and told the
session to reconcile it deliberately. It was not diverged: after a bounded
deepen, HEAD was an ancestor of origin by 429 commits and a fast-forward
brought it current. The harness had checked out a cached clone whose local
branch sat at a 2026-09-12 commit, and the guard that ran was that stale
tree's own copy — from before the fix gotcha g37 records. Same shape as g37,
recurring exactly as that entry says it will while the fix cannot reach the
tree that needs it; recorded here as a measurement, not a new gotcha. The
`AGENTS.md` this session was handed at startup was the stale one too (983
lines older than the tip), which is worth knowing: a session's instructions
file is read before any guard can move the checkout.

The deep check suite was green before the passes began — 204 passed / 0
failed, 48 passed / 0 violated, doc_lint, leak gate and doc_sync clean — and
green after them.

### Pass 1 — adopter installs

Four rehearsals, each run by a session that had not read this repository
and was told to follow the documents literally as the person they are
written for. Every finding was checked against the unlanded-branch inventory
first; none was already fixed on a branch.

**The guided install (SETUP.md → §1), as a non-technical administrator.**
The install audit passed; the other checks the documents name did not:

- **The light check went red on a file the administrator was told not to
  touch.** `templates/STYLEGUIDE.md.template` linked `deck/` three times,
  which in a consumer is `process/upstream/deck/` and in a §0 install is
  nowhere. Fixed: absolute upstream URLs, per
  [practice-links-travel](../practices/practice-links-travel.md).
- **`precedent_check.py` reported `1 violated` on a by-the-book install**:
  `github-setup-disclosed`, because
  [templates/GETTING_STARTED.md](../templates/GETTING_STARTED.md) named the
  workflow `doc-lint.yml` while every other document installs it as
  `bestpractice-docs.yml`. The previous run had changed that one line to make
  a §0 rehearsal pass. Fixed at the template.
- **SETUP.md contradicted itself three times** — "ask exactly three
  questions" against "they answer two", and "do not ask whether a brand
  guideline exists" against "ask whether a brand guideline exists" — and
  `VOICE.md.template` and `STYLEGUIDE.md.template` both carried an "At
  install, ask the administrator…" comment that survives into the installed
  file. All rewritten to say what "essentials only" says.
- **Nine numbered citations into the frozen catalogue** ("practice 38",
  "practice 12 in PRACTICES.md") across SETUP.md and INSTALL.md, in
  documents that themselves call that catalogue superseded. All repointed to
  slugs.
- **Smaller**: the workflow template unnamed ("install the Actions check
  from `templates/github-actions/`" — three files there); the repo's
  visibility asked of nobody yet gating the blocklist; `<administrator
  contact>` and two other placeholders sourced from no answer; "needs nothing
  from you but a name" for a name the adopter may not choose; "the two
  `freshness-guard.sh` commands" (there are three); `stop-git-check.sh`
  marked "Judgment" with nobody to judge; the branch to fetch unnamed; the
  jargon-gloss rule covering two words of the eight the administrator meets;
  `MAP.md.template` and `GLOSSARY.md.template` naming `CLAUDE.md` and a
  deduplicated practice; `bootstrap.sh` printing a false "single-branch
  clone" note on a repo with no remote. All fixed.
- **Recorded, not fixed**: the §1 adapter wires `reply-gate.sh` and
  `precedent-paths.sh`, so a §1 project ends every turn with `precedent gate
  FAIL` ([TODO 103](../TODO.md#classic-install-wires-loader-hooks)); the
  vendored tree carries this repo's `.github/workflows/`, `.claude/` and
  `local/` — 382 files in the install commit — appended to
  [TODO 101](../TODO.md#build-audience-dirs-still-vendor); and
  `commit-identity.sh` repoints the machine's `/etc/localtime`, which the
  rehearsal did to this container and could not undo (restored by hand; the
  hook table now says so).

**The §0 install, as a developer.** The loader came up (`OK`, 119
practices, resident ≈949 of 2000) and `precedent_check.py` reported
`1 violated` on a correct install:

- **`github-api-budget` fired on a tool the adopter never wrote.** The engine
  vendors `precedent_source_names.py` into every consumer; the registry that
  declares it is deliberately not vendored; the remedy ("copy one from
  upstream") produced a second violation about a budget for a tool the
  consumer does not have. The update rehearsal hit the identical pair.
  Fixed at the check: a caller listed in `tools/ENGINE_MANIFEST.json` or
  under `process/upstream/` was audited where it was written, and the
  remedy now says to write a registry for the repo's own tools. Pass 2
  question 1, exactly.
- **The bare light check checks nothing on a repo with no `origin`**, and
  the freshness guard refuses the session's first write on the same repo —
  so the dead links above were invisible until `--all`, and a freshly
  `git init`ed project is exactly the one with no origin. Both documents now
  say to lint the instantiated files by name and to give the repo an origin
  first; the mechanism is
  [TODO 104](../TODO.md#no-origin-is-not-stale).
- **§0's own text drifted**: its opening said the path "has not been
  rehearsed against a real project" while its closing paragraph recorded
  that one had, on 2026-09-14; step 1's engine list named fifteen files
  where the seed writes thirty-one; step 6 never said the sync writes
  `practices/`, `MANIFEST.json` and a test runner to the root that step 7
  then forbids; the `process/upstream` table missed four templates its own
  grep finds; the generated block's header names `build_views.py` as the
  regeneration command, which fails in a consumer. All fixed in the
  document; the header is
  [TODO 105](../TODO.md#consumer-hears-about-files-it-does-not-have)'s
  class, with the remedy strings that send a consumer to `templates/` and
  `spec/` it does not have, and the "treat this as unknown, not none" line
  printed on every prompt to an administrator who answered "none".
- **Recorded**: the vendored `doc_sync.py` ships this repo's `PAIRS` and
  three checks skip on modules the consumer seed omits
  ([TODO 106](../TODO.md#consumer-doc-sync-carries-upstream-pairs));
  `precedent-paths.sh` injects ≈11.6 kilobytes for a README edit (TODO 96 already).

**The migration, as a developer with a classic install.** The finished
repo resolved and synced cleanly (122 practices from four sources,
byte-identical on `--check`) — after two roadblocks:

- **Both skeletons shipped `practices/example-starter.md` with the same
  slug.** A migration that creates a team set and an individual set, as the
  document says to, then has its first sync refused: team outranks
  individual, so the individual set "contributed no practices at all". The
  harness had a case *built on* the shared slug, to exercise precedence.
  Fixed: the skeletons carry `example-starter-team` and
  `example-starter-individual`, the harness plants its own collision, and
  the document says to replace the placeholder before validating.
- **The document's tool paths flip** between `process/upstream/tools/` and
  the consumer's own `tools/`, which is empty until step 7 — step 5 as
  written cannot run — and `precedent_bootstrap_source.py` is not in the
  consumer engine, so the only copy a reader has records the *consuming*
  repo's commit as the new set's engine provenance. Fixed: a paragraph at
  the head of the pattern saying which copy each step runs.
- **Also fixed in the document**: "When this applies" read as if the loader
  were the rare case and the pack the common one; step 3 never mentioned
  `visibility` or `base_branch`; step 4 named a `settings.snippet.json`
  that has never existed; "mentions are fine" described a check that
  exempts files, not lines; the `exempt_files` example named a private
  record the reader was never told to write; "the old sync workflow" could
  not be told from the consumer's own; step 7 named no template; the
  decommission command omitted the pack manifest the audit refuses on; and
  step 8 now says what a clean migrated `precedent_check.py` run needs
  (five declarations no step created).

**The update, on a consumer vendored 2026-09-08.** The catalogue and
engine both came forward (85 → 119 practices, 21 → 31 engine files), and
the consumer then reported `2 violated` and warned at every session start:

- **The update never touches `tools/bootstrap.sh` or the hooks**, which are
  instantiated, not vendored — so the refreshed engine refused the bare
  `precedent_sync_views.py --check` the old bootstrap runs, and every session
  opened with a WARN naming a fix that failed the same way. Fixed two ways:
  `refresh` now ends by naming every wiring file still invoking the sync
  without `--repo` (verified against the rehearsal's own tree: ten lines
  named), and §2 has a step 0b for the wiring. `access-probe-is-wired` was
  the same cause.
- **The documented order was backwards** (catalogue, then engine) so the old
  checks read the new catalogue uncommitted and reported five false
  `acronyms-glossary` hits; "expect one refusal" promised a refusal that
  needs a retirement to fire; the post-refresh `--check` was framed as a
  confirmation and fails every time until the sync runs. All three
  rewritten, and the refresh trailer says the same.

**PARTIAL, for the third run running: no real consumer repository was
attached**, and this session did not ask for one at the top of the run
either — [TODO's `vdc-pass1-partial-again`](../TODO.md#vdc-pass1-partial-again)
already holds it. The rehearsals were run by sessions with no prior
context, which is closer to a real adopter than a fixture built by the
session that wrote the documents, and is what found most of the above.

**BOOTSTRAP DRIFT: 24 findings, none fixable from here.** All four sets
vendor the engine at `74eb776` (this checkout: `0b792c8`) and lack the two
files it gained since; every one is `HANDOFF`. The individual set's
`precedent/engine-refresh` branch is an unlanded refresh to `27655a1`,
already behind — the same shape the previous run closed.

### Pass 2 — mechanisms

- **Two definitions of "a command a person says".** The documentation
  currency scan took any capitalized `defines:` term; `precedent_vocabulary.py`
  reads the `command:` field. The scan reported "API budget" and "Relayed
  authorization" missing from the page doc_sync had just reported current.
  Fixed: one definition, the field. (Question 8.)
- **The instruction a session is told to follow cannot run.**
  `.precedent/SESSION_PRACTICES.md` ends with the loader's standing
  instruction — `python3 tools/precedent_show.py SLUG` — and not one of its
  fifty-six practices lives where that command reads; this session ran it
  for ten slugs and got ten refusals. `--repo DIR` has existed all along.
  Fixed: the file now ends with one line per source naming the command that
  works.
- **The check's own cost.** The tool reprinted the practice's Detail —
  ≈9,900 tokens, 46% of every run — beside an enumeration the session reads
  after loading that same Detail. Cheapened: a pointer by default,
  `--checklist` for the full text; the ledger table below records it.
- **Inherited state**: the session-start misdiagnosis above; a rehearsal's
  hook repointing this container's clock (restored). Nothing named `--check`
  wrote.

### Pass 3 — coherence read

- **Whole-tree lint clean** before and after; the leak gate clean.
- **Contradictions**: SETUP.md with itself (three), §0's opening with its
  closing, SETUP.md/FOR_DEVELOPERS ("§1 is the default") with ADOPTING.md
  (describing §0's layout to the same reader), README's "everything below is
  the pre-fork documentation" above sections rewritten for Precedent, the
  workflow filename in six places against one. All fixed; ADOPTING.md and
  README now say which layout the guided install produces and that `main`
  took the tree today.
- **Rules we ship somewhere else**: the two "At install, ask…" comments in
  `VOICE.md.template` and `STYLEGUIDE.md.template` were exactly the shape
  this bullet exists for — an instruction inert here and binding in every
  adopter, contradicting INSTALL.md's own "essentials only". Fixed. The
  hooks' rule-shaped lines were read and are about the mechanism, not the
  catalogue.
- **Keywords with no entry**: none; the vocabulary page carries all sixteen
  commands (the tool's report to the contrary was pass 2's finding).
- **Session load: 17,013 tokens across every repo in force**, this checkout
  10,550 — under the 20,000 target of TODO 82 and every declared ceiling.
  Nothing moved. Four gotcha entries mark their own trap settled; g37's
  fired in this very session, so it stays, and the other three were read
  against the tree last run and stand.
- **Tier placement: no change.** **Template freshness: one real gap** — all
  three team sets carry three files the team skeleton does not ship
  ([TODO 107](../TODO.md#team-skeleton-ships-three-files-short)).
  **Convergent drift**: the four sets share an older build, not a change
  the generator lacks — one diff against this checkout settles it.
- **Documentation currency**: five `REVIEW` prompts read; none a finding.

### Pass 4 — catalogue, backlog, and branches

**The phase-7 merge landed today, and this repository had not noticed.**
Alex merged [pull request #367](https://github.com/alex137/BestPractice/pull/367)
into `main` at 18:21 UTC, tree-identical to this branch at `3386318`; the
`EXPIRING PRACTICES` section asked whether
[merge-target-is-beta-branch](../local/practices/merge-target-is-beta-branch.md)'s
condition had happened yet, and it had. This branch has moved 64 commits
past that point since. `main` carries eight commits this branch lacks —
the merge, the revert-and-reapply pair that cancel, and `7d8f5a6`, whose
content PR #367's own carry audit found present here — so **nothing on
`main` is missing from this branch**, and the upstream watermark is moved
to `f4f9ac9` (`--by "PR #367"`) so the session-start notice stops naming
158 commits nobody needs to read. What is *not* done here is the switch:
where work lands next is Alex's and Morgan's call, recorded as `ask` in
[TODO 14](../TODO.md#retire-merge-target-practice) with the session's
recommendation (switch now; every day on the branch is another fold-in to
rehearse).

**Endgame merge: 0 conflicts, 0 silently absent**, on a clone deepened to
the real merge base — the two conflicts the previous run recorded were
resolved in PR #367 itself.

**Branch verdicts.**

- `alex137/BestPractice: open-item-and-gotcha-plan` — 4 commits, all today,
  Morgan's; adds
  `spec/OPEN_ITEM_AND_GOTCHA_PLAN.md` (613 lines): one open item per file,
  filed by kind, every list generated, with his nine answers recorded. It is
  the answer to the finding this run would otherwise have filed — `TODO.md`
  is 6,750 lines and 130 items, and no session reads it end to end. **Land
  it** — live work in progress, not a stale branch.
- `alex137/BestPractice: claude/file-sharing-service-spec-0m9c7p` — unchanged;
  [issue #394](https://github.com/alex137/BestPractice/issues/394) holds the
  ask to Alex.
- `themorgan/precedent-individual: claude/quirky-pasteur-e997ei` — 1 commit,
  today, retiring the weekly engine-refresh cron in that set and keeping the
  job on demand — the same decision Morgan made here. **Merge** (HANDOFF).
- `themorgan/precedent-individual: precedent/engine-refresh` — a refresh to
  `27655a1`, already 60-odd commits behind. **Close** (HANDOFF); refresh
  fresh instead.
- `themorgan/precedent-individual: precedent/engine-refresh-c6c885033a9f` —
  **Close**, as two runs already decided.
- **Merged and not deleted**: 10 branches stale (≥ 30 days) and ≈60 recent,
  all proven by the ancestor test; deletion is refused to a session by the
  permission classifier (recorded last run) and stays Morgan's chore.

**Live sessions**: 25 on the account in the window; one running (this),
two idle (a vendor update in a consumer repository not in force here; an
"Instructions" session on this repository idle since 18:43 UTC). No session
is mid-way through anything a repo in force shows as half-done.

**The full catalogue read is recorded as NOT DONE**, for the reason the two
previous runs gave: it is `full-practice-audit`'s own on-request job and
reporting it done on a skim is the failure that practice exists to prevent.
**The private sets' backlogs were not swept**, same as before.

## What Each Part of the Check Returned, and What It Cost

Every run appends itself to
[../record/very-deep-check-ledger.json](../record/very-deep-check-ledger.json)
— one row per section: what it found, what it printed (in tokens, the same
words × 1.3 estimate used everywhere else here), and how long it took — and
prints the cross-run read at the end of the run. **Never hand-edit it**: it
is written by
[../tools/very_deep_check.py](../tools/very_deep_check.py), and a figure
typed into it by hand is a figure nothing measured.

**GITHUB API BUDGET is the newest section, added 2026-09-14** on Morgan's
request, after a session was refused by GitHub with a rate-limit error. It
prints last — the run's own API bill is only complete once every section that
calls the API has finished — and it costs nothing extra to take, because the
headroom it reports is read off the `X-RateLimit-*` headers of calls the run
already made. It has no entry in the table below yet and should not get one
until it has run quiet across several runs; the practice behind it is
[github-api-budget](../practices/github-api-budget.md).

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
| REPOSITORY VISIBILITY | 2026-09-11 | **cheapen** | The only expensive quiet section: ≈1,738 tokens, 10% of the run's output, and 26 of its 28 lines this run were the identical "GitHub access to this repository is not enabled for this session" sentence repeated per repository. The check is worth keeping — a private repository name reaching a public tree is the failure it exists for — but a session does not need that sentence 26 times. Collapse the unreachable ones to one line with a count and the names, and print the full paragraph only for a repository whose visibility was actually determined. **Approved by Morgan and done, 2026-09-13** (`strength: decided` — *"let's do it, approved, that's lots of tokens ... that aren't needed"*): `repo_visibility_audit` now groups every unreachable repository by the reason it could not be checked and emits one line per reason, carrying the count and every name. Re-measured the same day: 34 lines became 1, and the two determined repositories still print in full. |
| CHECKLIST — the four passes a session works | 2026-09-14 | **cheapen** | Not quiet — it is the costliest section on the page, ≈9,900 tokens a run (46% of the output), and it is a verbatim copy of the practice's Detail, which a session loads with `precedent_show.py very-deep-check --detail` before it can work a pass at all. Since 2026-09-14 the section is a four-line pointer and `--checklist` prints the text (`strength: assented` — the session's own reading of the ledger, not an instruction). |

## Runs so far

| Run | Passes completed | What it changed |
|---|---|---|
| 2026-09-14 | 1 (partial), 2, 3, 4 (partial) | On Morgan's direct request, with the adopter experience as the brief. Four literal rehearsals by sessions with no context — the guided SETUP.md install, a §0 install, a migration, a six-day-old consumer's update — found 65 defects, eight roadblocks; every one fixable from here was fixed the same day (a skeleton slug collision that refused a migration's first sync, an API-budget check firing on every fresh consumer, a template's dead links going red on the adopter's first check, the update leaving every session start warning). The dominant finding is a decision: the guided default installs §1, which turns on none of the loader the pitch describes. Pass 4 found the phase-7 merge into `main` had landed that day unnoticed; its retirement item is now `ask`. Pass 1 partial (no real consumer attached, third run running); the full catalogue read not done. |
| 2026-09-11 | 1 (partial), 2, 3, 4 (partial) | On Morgan's direct request. Every finding one shape: a mechanism changed and the sentences describing it did not. `precedent_sync_views.py` made `--repo` mandatory and seven documented invocations still omitted it — including the one running in every adopter session and the one shipped into every adopter repo. INSTALL.md §2 had no step for a §0 install's practice catalogue, so a consumer taking the documented update kept 72 practices against upstream's 98 and reported `OK`. Two checks that could not pass on a correct fresh install (`github-setup-disclosed`, `acronyms-glossary` — the latter measuring its vocabulary from tracked markdown, so it reported words from the vendored catalogue). One shipped template restating four catalogue rules as its own, one of them resident. And the phase-7 merge, recorded at 0 conflicts, re-rehearsed at 2. Pass 1 partial (no real consumer attached); pass 4's full catalogue read recorded as not done. |
| 2026-09-08 | 1, 2, 3, 4 | Ahead of showing `precedent-beta-v01` to Alex. Six defects, all fixed and pushed: the unlanded-work scan fabricating work on a shallow clone; `seed` and `refresh` between them leaving a renamed-away engine file in every adopter's tree, permanently; the withdrawn-practices table linking a successor that lives in another source, which failed a team set's own light-check; a session whose hooks never ran, so 53 private practices were silently not in force; the checkout being moved off its working branch mid-session (cause NOT found — detector added); and this practice's own pass-3 bullet instructing a session to reverse a decision Morgan made that morning. All three practice sets refreshed onto the current engine and their orphaned file removed. |
| 2026-09-07 | 1, 2, 3, 4 — all four | The first run to complete all four passes under this practice. ≈30 defects found and fixed across four repositories: 6 in pass 1, 8 in pass 2, the rest in passes 3 and 4. Shipped `internal_paths` and `output_paths` for headline scoping, two content-corruption fixes in `title_case.py`, the failure recap in `verify_harness.py`, a hermetic fixture, the merge-commit backstop, commit identity reaching every attached repo, the within-source conflict scan, and `tracked-practice-files`. Promoted `fail-gracefully` and `bold-key-phrases` to universal, ending two same-level collisions. Pass 4's 53 sequential judgments deliberately not run — see the closing note. |

The 2026-09-06 [pre-launch audit](PRELAUNCH_AUDIT.md) is the closest thing to
a prior run, and is where pass 1's method and all but one of pass 2's
questions come from — it was not run under this practice, and its own
still-open list is a separate document, kept there rather than copied here.
