---
title:         "Plan: Scope verify_harness.py's slowest checks to what actually changed"
kind:          proposal
status:        drafted
opened:        2026-09-16
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       "Two scoping changes to verify_harness.py's push gate, drafted from a chat brainstorm and backed by measured commit-history data, awaiting review and authorization before implementation."
---
# Plan: Scope verify_harness.py's slowest checks to what actually changed

Self-contained: a session with no memory of the conversation that produced
this can carry it out from this document alone.

**Status: drafted, not yet reviewed or authorized. Nothing described here
has been implemented.** This follows on from
[spec/VERIFY_HARNESS_PERFORMANCE.md](VERIFY_HARNESS_PERFORMANCE.md), which
measured the push gate at 250.7s, then 192.9s after a change-scoping fix to
three [tools/very_deep_check.py](../tools/very_deep_check.py) regression
tests. This document covers the two
items that session left open, worked through in a follow-up chat, with
several early ideas tested against real history and revised or dropped when
they didn't hold up.

## Background: is `check_precedent_check_fires` someone's deliberate rule, and does the incident it guards against exist?

Before proposing to weaken this check's coverage, the incident it exists to
catch was verified rather than taken on faith, and its authorship was
checked.

**The incident is real**, not a plausible-sounding story. Commit
`f0c5070b` ("Build the enforced channel, and find that none of the eight
claims was one," 2026-08-31) names the specifics: `readers-vocabulary`
pointed at a linter with no vocabulary check in it; `acronyms-glossary`
named a check that only ever warned; four more named gates that were
already red or vacuous on this repository, for reasons unrelated to the
practice claiming them. The commit verified this empirically, not just by
assertion: after building the 18 real checks, it neutered the entire
registry (every check made to return no findings) and reran the harness to
confirm it correctly reported all 18 as broken.

**Authorship**: the commit's author identity is `Morgan F`, matching this
session's own git identity, dated 2026-08-31 — after the 2026-03-06 date
marking sole use of this account, so
within Morgan's own tenure, not the prior employee's. No evidence of Alex's
involvement was found in the commit itself or its merge history. What
cannot be established from the repository: whether this specific test
design (a planted violation, in both directions, for all 61 enforced
practices, every run) was deliberately chosen versus proposed by the
session and approved without scrutiny of that specific choice. Per
[practices/decision-strength.md](../practices/decision-strength.md), that
is recorded as **unknown**, not as a decision — no quote of it being chosen
exists to cite.

## Proposal 1: scope `check_precedent_check_fires` by dependency, not blanket

### Current behavior

[tools/verify_harness.py:5353](../tools/verify_harness.py) (`check_precedent_check_fires`)
runs unconditionally on every push. It builds 61 `case()` calls — one per
enforced practice — each copying the full tree twice (`shutil.copytree`)
and launching [tools/precedent_check.py](../tools/precedent_check.py)
`--only <slug>` twice, once against
a planted violation and once against a clean copy. Measured cost: 90.2s,
36% of the 250.7s baseline. The function's own closing assertion
(`tools/verify_harness.py:7432`) checks that `set(pc.CHECKS) - set(planted)`
is empty — full coverage of every registered check is the point of the
function, not incidental to it.

### Why "only test what changed" is the wrong first cut

None of the eight original broken claims broke because someone edited that
practice's own file. They rotted because something shared under them
drifted — a linter's vocabulary check that was never wired in, a shared
script that went red for unrelated reasons. Scoping this check to "did the
practice's file change" would reopen exactly that blind spot: on an
ordinary push that touches none of the 61 practice files, none of the 61
cases would run, for however many pushes until one happens to touch that
file.

### The design

Three tiers, replacing the single unconditional sweep:

1. **A practice file's own `checked_by:` / `## Rule` changed** → retest
   only that practice's case. (An earlier draft of this plan put this in
   the full-sweep bucket by mistake — see the measurement below for what
   that mistake cost.)
2. **A shared script a `checked_by:` points at changed** — the four
   inherited scripts [tools/doc_lint.py](../tools/doc_lint.py),
   [tools/doc_sync.py](../tools/doc_sync.py),
   [tools/practice_audit.py](../tools/practice_audit.py),
   [tools/model_audit.py](../tools/model_audit.py), each backing several
   practices via a shared helper (e.g. `_doc_lint()` at
   `tools/precedent_check.py:3425`, called by multiple check functions) —
   → retest only the cases that declare a dependency on it. This needs one
   new piece of bookkeeping: an explicit `depends_on: [...]` field on the
   ~10 affected `CHECKS` registrations, hand-declared the same way
   `checked_by:` is already hand-declared on practice files — not inferred
   by scanning function bodies, which would be fragile and silently wrong
   the moment a check is refactored. Materialized scripts under
   `tools/checks/*.py` need no such map: `register_materialized_checks`
   (`tools/precedent_check.py:394`) already assigns exactly one slug per
   script file.
3. **`tools/precedent_check.py` itself changed** → full 61-case sweep, no
   narrowing. This file is the shared engine every one of the 61 cases
   executes through; narrowing this trigger further (e.g. parsing which
   function inside it changed) risks the same silent-narrowing failure the
   whole check exists to prevent, for a file that is already a small share
   of pushes (below).

The full, unconditional 61-case sweep moves to
[tools/very_deep_check.py](../tools/very_deep_check.py) as a new on-demand section, so drift that hits none of the three triggers
above (an environment change, a dependency neither `checked_by:` nor
`precedent_check.py` names) is still caught periodically rather than never.

### Measured, not estimated

Pulled from real history on `precedent-beta-v01`: 1,568 commits, 434
merges/pushes (each diffed against its own first parent).

| Touches… | % of pushes (of 434) |
|---|---|
| `tools/precedent_check.py` (irreducible full-sweep trigger) | 14.1% (61) |
| one of the 4 legacy shared scripts | 6.7% (29) |
| `tools/checks/*.py` (already 1:1, no map needed) | 0.0% (0) |
| any `practices/*.md` | 31.3% (136) |
| **only** a `practices/*.md` file, nothing else | 20.7% (90) |

The naive version of tier 1 (routing any practice-file change to the full
sweep) would have cost those 90 pushes — 20.7% of all pushes — a full 61-case
sweep for no reason; each only ever needed its own single case. With tiers
1-2 fixed to go narrow and only tier 3 left as a full-sweep trigger, the
full-sweep rate drops from the **38.9%** an earlier, cruder version of this
proposal measured out to, down to **14.1%** — the `precedent_check.py`-only
floor. Average saving across the push gate: roughly 0.86 × 90.2s ≈ 78s off
an ordinary push, versus roughly 0.61 × 90.2s ≈ 55s under the cruder version.

This repository is unusually practice-file-heavy since it is the practice
engine itself; a repository that only vendors it would very likely see a
lower trigger rate on all three tiers.

### Accepted gap

Same shape as the gap `_changed_touches()` already documents
(`tools/verify_harness.py:300`) for the `very_deep_check.py` tests: this is
scoped to the direct files named at each call site and each check's
declared `depends_on:`, not their full transitive import closure. A change
to a helper module one of the four legacy scripts imports, which alters
its behavior without touching the legacy script itself, would not be
caught by the push-gate version — only by the on-demand full sweep now
living in `very_deep_check.py`. Enumerating that closure by hand was
rejected for the same reason it already was for the `very_deep_check.py`
checks: it goes stale the moment those imports change, and a check that
silently narrows itself is worse than one that says plainly what it does
not cover.

## Proposal 2: keep the push-gate self-test mandatory; cut local iteration cost instead

### What was proposed first, and why it doesn't work

The original idea (matching the intent that
[tools/verify_harness.py](../tools/verify_harness.py) = routine
push gate, [tools/very_deep_check.py](../tools/very_deep_check.py) =
manual/occasional) was to move
`check_very_deep_check_bootstrap_drift`, `check_very_deep_check_convergent_drift`,
and `check_shallow_clone_never_fabricates_unlanded_work`
(`tools/verify_harness.py:19558`, `:19687`, `:20861`) out of the push gate
entirely and into a self-test step inside `very_deep_check.py`'s own `_main()`
(`tools/very_deep_check.py:4220`), scoped to only the files a given edit
touched.

Tracing the actual mechanics kills this: the scoping helper
(`_changed_touches`, `tools/verify_harness.py:300`) compares the current
branch against `origin/<default-branch>` — committed-but-unmerged commits
plus worktree changes. Once an edit to `very_deep_check.py` merges into the
base branch, that comparison shows no diff. So a self-test living inside
`very_deep_check.py`'s own invocation would only ever fire in the narrow
window where the edit is still local and unmerged, and only if someone
happens to run `very_deep_check.py` manually during that exact window. If
an edit is pushed without that manual run happening first, **the self-test
never fires for that change, at all** — not later, not on the next
periodic sweep. It also provides no actual speed win over what already
shipped: the current push-gate version already costs ~14ms on an ordinary
push and only pays the ~70s when the relevant files change, which is the
same cost profile this move was chasing.

### The design that survives the trace

Leave `check_very_deep_check_bootstrap_drift`,
`check_very_deep_check_convergent_drift`, and
`check_shallow_clone_never_fabricates_unlanded_work` in
`tools/verify_harness.py`'s push gate, unconditionally required before a
branch goes out — this is the only mechanism that guarantees they run at
least once for every edit to the files they protect. Add a flag (working
name `--skip-vdc-selftest`) that a developer can pass on **local,
intermediate** runs while actively iterating on `very_deep_check.py` or
[tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py),
so repeated local test runs don't
each eat ~70s. The push/CI-gating invocation does not pass this flag and
always runs the full self-test — the "always catches it before it lands"
guarantee is unchanged.

### Implementation notes

- Add `--skip-vdc-selftest` to
  [tools/verify_harness.py](../tools/verify_harness.py)'s argument
  handling; each of the three checks' `_changed_touches(...)` gate
  (already in place) additionally short-circuits to `not_applicable(...)`
  when the flag is passed, with a message naming it as a local-only skip,
  not a scoping decision.
- No change to what runs at push/CI time.

## What this plan does not change

- The push gate's guarantee that every registered check has a planted
  case (Proposal 1's tier 3) and that `very_deep_check.py`'s own logic is
  tested before a change to it lands (Proposal 2) are both preserved, not
  weakened.
- The three already-shipped `_changed_touches` skips from
  [spec/VERIFY_HARNESS_PERFORMANCE.md](VERIFY_HARNESS_PERFORMANCE.md)
  (merged via PR #427) are untouched by this plan.

## Status and next step

Drafted from a chat brainstorm; not reviewed, not authorized, nothing
implemented. Awaiting review. On authorization, this document's `status`
moves to `accepted`, the two proposals are implemented against the file
and line references above, the full deep-check suite
([tools/verify_harness.py](../tools/verify_harness.py),
[tools/doc_lint.py](../tools/doc_lint.py),
[tools/leak_gate.py](../tools/leak_gate.py),
[tools/precedent_check.py](../tools/precedent_check.py),
[tools/doc_sync.py](../tools/doc_sync.py)) is run to confirm
`0 failed`/`0 violated` and to
re-measure the timing claims above against the real change, and `status`
moves to `executed`.
