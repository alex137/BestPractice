<!-- Last updated: 2026-09-04, phase 1 landed -->

# The Practice Simulation (Brief)

**Status: approved; phase 1 (rough phasing, below) is built.** Written up per
Morgan's request to have a plan to approve before implementation starts.
Treat this the way `spec/PHASE5_BRIEF.md` and friends were treated
— a brief a phase is built from, updated in place as it's actually built,
not superseded by a second drifting copy.

## The question this exists to answer

Morgan wants a command — eventually reachable the way `precedent show` and
`precedent gate` are — that reports something like *"of the practices that
should have fired, how many did; of the ones that fired, how many produced
a correct result"* — and that he can run **regularly** to track whether
routing is getting better or worse over time.

## Why the existing tools don't already answer it

- [tools/behavioral_replay.py](../tools/behavioral_replay.py) is cheap and
  mechanical but only covers the ~23 practices with a real `applies_to`
  glob, and never asks whether guidance was *followed* — only whether it
  would have been *shown*.
- [tools/routing_eval.py](../tools/routing_eval.py) already measures both
  recall and (loosely) correctness, oracle/control/treatment, but it
  replays a fixed set of 20 historical commits from this repo's own past.
  That's the design flaw this brief exists to fix: a fixed replay set is
  something the loader's own inputs get tuned against — the v5 round in
  [spec/LOADER.md](LOADER.md) already shows a glob pass "converting reach
  failures into judgment failures" on the *same* 20 cases. Optimizing a
  design against the thing that scores it is Goodhart's law, not
  validation. It also can't say anything about how routing behaves on a
  dependent repo's own file layout, conventions, or source precedence —
  it has only ever run against this repo.

## Design

### 1. Generate scenarios, don't replay them

For each practice's `occasion` (or, for path-triggered ones, its
`applies_to` scope), a generator persona invents a plausible, fictional
task that should trigger it — not a summary of a real commit, an
independently authored situation. This decouples the test set from any
fixed history and means a fresh batch can be produced every run instead of
scoring the same cases repeatedly.

### 2. Negative and near-miss cases, deliberately

For every real scenario, also generate: (a) a distractor that sounds
similar but shouldn't trigger the practice, and (b) cases straddling two
confusable practices (e.g. `convention-to-audit` vs. `mistakes-become-rules`
— both about a violated rule, different triggers). Real history rarely
hands you clean confusable pairs on demand; synthesis can manufacture
exactly the boundary the routing design needs to prove it can hold.

### 3. Adversarial generation

Rather than a single generator producing "the obvious example," a separate
pass asks a generator to invent the case *most likely to fool the router*
for a given practice — surface cues pointing elsewhere, or an easy-to-miss
framing. This targets the design's weak points instead of its average
case, which is what a benchmark you intend to trust needs.

### 4. Rotate the set; never let it become a fixed benchmark

Each run reseeds scenarios (different fictional domain, different
phrasing) rather than reusing a saved case bank. Improving the score then
requires improving the actual routing logic — the occasion index wording,
the globs, the resident set — not hand-tuning against twenty known
answers. This is also what makes "run it regularly" mean something: a
trend line across rotating batches, not a number that stops moving once
it's been fit once.

### 5. Score correctness two ways, and say which is which

- **Mechanical, where a proven `checked_by` exists.** For the ~26 checked
  practices (and only the ones `check_precedent_check_fires` actually
  verifies fire in both directions — see the `checked_by` explanation
  above), have the agent under test actually perform the synthetic task
  and run the real check script against its output. Objective, free of
  grader bias, no LLM judgment involved.
- **Judged, for everything else.** The remaining prose-only practices need
  an LLM verdict on whether the produced work actually satisfies the
  Rule. Report this separately from the mechanical score rather than
  blending them into one number — they have very different reliability,
  and blending them would hide which one moved.

### 6. Test against attached repos, not only this one

This is the part current tooling has never done at all. Routing is
repo-shaped: a glob like `templates/**` means "where this repo keeps
practice text" here and "the host's own files" in a dependent repo (this
exact gap is already called out in
[spec/ENFORCEMENT.md](ENFORCEMENT.md)'s `practice-export-loop` section).
A simulation that only ever runs against BestPractice's own tree cannot
tell us whether routing holds up anywhere else, and the cross-source
resolver ([spec/SOURCES.md](SOURCES.md)'s precedence, universal + team +
individual + repo-local) has only been tested against one synthetic
fixture, never a real consumer repo with real content.

So: for each repo attached to a simulation run —

- Generate scenarios using **that repo's actual file tree and
  conventions** (real paths, real naming, real language/stack), not
  BestPractice's own — so path-glob matching is exercised against layouts
  it wasn't written against.
- Materialize that repo's actual resolved practice set (universal + its
  own team/individual/repo-local sources, via the same
  `precedent_materialize.py` / `precedent_sync_views.py` path a real
  install uses) rather than assuming BestPractice's catalogue applies
  as-is.
- Score routing **and** precedence together: does a repo-local override
  actually take priority over the universal practice it overrides, in a
  scenario built to exercise that.
- Report **per repo**, not only as one rolled-up average — a regression
  on one dependent repo's routing shouldn't be invisible inside a mean
  across several.
- Scenario generation still follows the "don't replay history" rule from
  §1 — a dependent repo's own past commits are as susceptible to
  overfitting as this repo's are. The repo's tree and conventions are the
  input; its git log is not the source of the test cases.

This needs a maintained list of attached repos to run against (repos this
session or a future one has `add_repo`'d, or a small fixture list of real
dependent repos that have opted in) — an open question in the phasing
section below, not decided here.

### 7. Cadence — two tiers, not one command pretending to be both

- **Light / frequent.** Mechanical-only: `behavioral_replay.py`'s existing
  reach measurement, plus the new mechanical correctness scoring from §5,
  against this repo. Free, fast, safe to run on every push or as a
  standing `precedent simulate --quick` command.
- **Full / periodic.** The synthetic generation + negatives + adversarial
  hardening + judged scoring + attached-repo pass from §1-6. Costs real
  LLM calls, run weekly or monthly (or on demand) rather than per-push —
  `precedent simulate` with no flag, or `precedent simulate --full`.

Both report into one running log (a generated block, following
`docs-track-models` — figures live in a script's output, not retyped into
prose) so the trend is visible over time, the way `spec/LOADER.md`
currently narrates routing-eval rounds by hand.

## What this keeps from existing infrastructure vs. what's new

| Piece | Status |
|---|---|
| Mechanical path-glob replay | Kept — `behavioral_replay.py`'s reach measurement, unchanged, folded into the light tier |
| Oracle/control/treatment three-arm structure | Kept as the shape, but driven by generated scenarios instead of a fixed 20-commit set |
| Isolation between hops (no repository access, so the index can't be sidestepped) | Kept from `routing_eval.py` |
| `checked_by` mechanical scoring | New — routing_eval today judges applicability, never runs a real check against the output |
| Synthetic generation, negatives, adversarial cases, rotation | New |
| Multi-repo testing | New |
| Two-tier cadence with a running trend log | New |

## Open questions (for you, not decided here)

- Which repos count as "attached" for §6 by default — anything the session
  has added this run, or a maintained opt-in list? Real dependent repos
  vary in how much they want a simulation harness poking at their tree.
- Budget for the full tier — how many synthetic scenarios per run is
  worth the LLM cost, and does that scale per attached repo or stay fixed
  regardless of how many are attached?
- Where the "generator" and "judge" roles should be different
  models/personas to reduce the risk of one session's blind spots
  producing both the test and its own passing grade.

## Rough phasing

1. **Built.** Mechanical correctness scoring against proven `checked_by`
   checks, folded into `behavioral_replay.py` as `--with-checks`
   (`--max-correctness-commits N` bounds it, default 25 — each sampled
   commit is checked out into a scratch git worktree and run through
   *that commit's own* `tools/precedent_check.py`, since older commits
   predate some checks entirely). Trusts only the slugs
   `verify_harness.py`'s `check_precedent_check_fires` actually proves
   fire both ways (read from its own `case(...)` registrations, not
   hand-copied, so this can't silently drift) — 26 as of this writing —
   and only in `tree`/`change` scope (`turn-end` checks are about live
   session state, never exercised by a historical `--range` replay, and
   would misreport as a false 100% pass rate if counted). A first run
   against this repo's own history found 2 real, live violations in
   `acronyms-glossary` and `index-remembers-past` out of 114 (commit,
   check) data points sampled — genuine signal, not a smoke test.
   Deliberately narrow: this measures retrospective enforcement
   compliance for the ~26 checked practices only, nothing about the other
   ~31, and nothing about routing or intent.
2. Synthetic scenario generation (§1-4) against this repo only, replacing
   `routing_eval.py`'s fixed case set — proves the generation approach
   before adding repo-count as a second axis.
3. Multi-repo pass (§6) once (2) is trusted on this repo alone.
4. Wire both tiers into a single `precedent simulate` command and the
   running trend log.
