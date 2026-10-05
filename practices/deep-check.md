---
slug:        deep-check
title:       "The deep check: every audit, plus an open-ended coherence review"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A person asking for a deep check is a moment, not a file, and the read covers the whole repository; the occasion index reaches it, and its check reads tools/checks/ on every run."
occasion:    "asked for a \"deep check\""
gates:       ["merge"]
index_clause: "every mechanical audit, plus a full read of the repo against itself"
index_required: true
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "pending PR review -- drafted 2026-10-05 by Morgan F, moved from the shared set precedent-shared-repo-maintenance"
strength: decided
---
## Rule
Where a repo's [`two-check-levels`](https://github.com/alex137/BestPractice/blob/staging/practices/two-check-levels.md) names its push suite "deep check", that suite is this practice's mechanical half; the review half runs only when a person asks for a deep check by name, never as part of a push. A deep check has two halves. The mechanical half is every audit script the repo maintains, run together -- the same set the merge runbook already runs on every merge, and all of it must pass before the merge commits. The review half is a read of the repo's own rules and documents against each other -- the audits catch broken links and bad syntax; they can't catch a rule that now contradicts another rule, or a section that stopped making sense a few edits ago.

**Mechanical before human, every time.** Run the mechanical half first and fix what it reports *before* the review reads a line: judgment spent on what a script already catches is wasted, and a tree already failing its own gates makes every later finding ambiguous -- you cannot tell drift this pass introduced from drift that was already there.

## Detail
What to look for -- a starting point, not a specification: contradictions between rules; stale references (a slug, filename, or click-path pointing at something moved or gone; a positional number cited as if it were a name); fragments left by an earlier edit; the same rule restated in several places; disproportion, in a document's own weighting and in a rule's running cost -- especially one re-researched from scratch each time instead of following a written-down answer; formatting drift (heading levels and capitalization, ragged tables, a stale header); a rule this set asks of every project it installs into that it doesn't follow itself; and backlog entries already done. Anything else the read turns up is still a finding -- report it, and add a bullet here if it will recur.

Fix what the review turns up in the same pass, then re-run the mechanical half, since the fixes break links of their own. Anything deliberately left alone gets a line in the backlog document.

When it runs: the mechanical half on every merge, per the runbook. The review half only when a person asks for a deep check by name. After work that invites drift -- rules added or reordered, a rule that changed shape, an install into a new repo, or a merge that resolved conflicts across several shared files -- say that a deep check would be worth asking for; don't run the review half unasked.

## Why
It is deliberately not a per-commit gate: the review half costs a careful read of the whole repo, which is exactly why the light check exists to carry the cheap checks on every commit instead.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration.

**Retired 2026-09-05, un-retired 2026-09-06.** The retirement rested on a
single premise: that BestPractice's universal
[very-deep-check](https://github.com/alex137/BestPractice/blob/staging/practices/very-deep-check.md)
was this practice under another name. That premise came from
`very-deep-check`'s own Story, which describes this practice as
"generalized ... but otherwise the same enumeration as here," and it is
wrong. Morgan settled it on 2026-09-06: **the two are unrelated rules, and
the deep check keeps happening in sessions when committing, as it always
did.** They answer different questions at different cadences -- this one is
the working check a session runs against its own repo as part of landing
work; the very deep check is a rare, expensive, cross-repo audit of the
whole Precedent system, "deliberately rare because the judging is
expensive" by its own Rule, and explicitly "never wired into a commit,
push, or merge gate." Retiring this one on the strength of that one removed
a routine check on the authority of an occasional one.

Nothing was lost in the interval, but only by accident: `precedent_gate.py`
does not read `status`, so the merge gate kept serving this practice in
full the whole time it was marked retired. That is a bug compensating for a
gap, not a safety net, and it is written up for BestPractice separately.
Restored to exactly what it was -- Rule, Detail, cadence and
`checked_by` untouched -- rather than rewritten, since what was wrong was
the decision to retire it, not the practice.

**Reviewed 2026-09-06 against `very-deep-check`'s four-pass restructure**
(BestPractice's TODO item `roll-out-four-pass-restructure`), and **one thing
was adopted from it: the mechanical-before-human ordering now in the Rule.**
That idea is cheap, single-repo, and fixes a real gap here -- this practice
already said to re-run the mechanical half *after* fixing review findings,
but never said to run it *first*, which is the half that keeps a finding
attributable.

**The four passes themselves were deliberately not adopted.** Passes 1, 2
and 4 are cross-repo and expensive by design -- adopter installs built from
scratch, an audit of whether every mechanism reports what it claims, a full
catalogue sweep -- and the universal practice that owns them says outright
that it is never wired into a commit, push or merge gate. This one is, on
every merge. Folding them in would erase exactly the line `two-check-levels`
draws between what gates a merge and what a person asks for by name. Pass 3,
the coherence read, is the only one that overlaps, and this practice's own
Detail already covers substantially the same ground.

Nothing was pointed at via `overrides:`, per Morgan's ruling above that the
two are unrelated rules: there is nothing here to override.

**Reviewed again on 2026-09-28, against universal's `two-check-levels` and `very-deep-check`, and left here.** Morgan had approved merging overlaps into universal where they were true duplicates, and this is not one. `very-deep-check` is the rare, cross-repo audit Morgan ruled on 2026-09-06 to be an unrelated rule. `two-check-levels` names the two levels and says the full one gates a merge; it does not say what a deep check contains. The coherence read, the what-to-look-for list and mechanical-before-human are this practice's own.

**2026-10-01: occasion shortened to the spoken trigger** (Morgan, in the
reduction pass: *"Question 3 - all are great, approved"*, strength:
decided). It used to add "or after drift-inviting work", which contradicts
the Rule's own line that the review half runs only when a person asks for a
deep check by name. The mechanical half needs no index line for that: it
runs at every merge through this practice's merge gate and the push check.

## Install
Checked mechanically, but only half of it: [tools/precedent_check.py](../tools/precedent_check.py)'s `deep-check` check, scope `tree` (ported on 2026-10-05 from the shared set this practice moved from), verifies the mechanical half's own claim is actually true -- that `tools/checks/tests/run_all.sh` really does run every audit script the repo maintains. It catches a check script added with no matching test (so `run_all.sh`'s `test_*.sh` glob would silently never exercise it) and a stale test left behind after its check script was removed. The review half -- reading the repo's own rules against each other for contradiction, drift, or disproportion -- is explicitly the part no audit can catch (per this file's own Rule: "the audits catch broken links and bad syntax; they can't catch a rule that now contradicts another rule"); that's a judgment call by design, not a gap to close. It skips in the engine's own origin, which has no materialized check family. Its planted case in `tools/verify_harness.py` adds a `run_all.sh` and a check script with no test.

