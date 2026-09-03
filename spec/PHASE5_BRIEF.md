<!-- Last updated: 2026-09-02 (Buenos Aires) by the phase-5 build session -->

# Phase 5 Brief — The Creation Pipeline

**Status: phase 5's tooling is built and harness-tested, as of 2026-09-02.**
Read [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s "How a Practice
Comes Into Existence" section first — this brief is the implementation note,
in the same relationship [spec/ENFORCEMENT.md](ENFORCEMENT.md) has to phase
4. The done-when this phase actually delivers: **a candidate can be raised,
promoted and landed end to end; a candidate failing any of the four
criteria is refused with a reason** — proven directly by
`check_creation_pipeline_fires()` in
[tools/verify_harness.py](../tools/verify_harness.py), not merely asserted.

## What got built, stage by stage

| Stage | Tool | What it does |
|---|---|---|
| 2 — Candidate | [tools/precedent_candidate.py](../tools/precedent_candidate.py) | create / list / expire, against the schema [spec/CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md) documents |
| 3 — Promotion criteria | [tools/precedent_promote.py](../tools/precedent_promote.py) | the four criteria, each refusing with a named reason |
| 4 — Approval | [tools/precedent_land.py](../tools/precedent_land.py) (individual/universal), the pre-existing `approvers.json`/`CODEOWNERS` in `precedent-team-maintainers` (team) | see "Stage 4's actual scope" below |
| 5 — Landing | [tools/precedent_land.py](../tools/precedent_land.py) | writes the file, hard-refuses an unregistered `checked_by` |
| 1 — Detection | [tools/precedent_detect.py](../tools/precedent_detect.py) | the mechanical signals that don't need a live conversation or a trip-log |
| 6 — Retirement | [tools/precedent_retire.py](../tools/precedent_retire.py) | the periodic report — proposes, never acts |

**Built out of Stage order** (2 → 3 → 4 → 5 → 1 → 6, not 1 → 6): the data
model and its consumers were built before the producer that feeds them, so
each stage could be tested against a hand-raised fixture candidate before
Stage 1's detection existed to raise one automatically. Stated here because
it is a real departure from the plan's own numbering, the same way phase 4
disclosed its own departures rather than leaving them to be discovered.

## Three pre-build calls, made before any of this was written

Recorded in full in
[decisions/2026-09-02-phase-5-preflight-calls.md](../decisions/2026-09-02-phase-5-preflight-calls.md),
with the substantive reasoning living in the artifact each one governs:

1. **Retirement is approval-gated, exactly like creation** —
   [PRACTICE_ENGINE_PLAN.md, Stage 6](../PRACTICE_ENGINE_PLAN.md#stage-6--the-loop-closes).
2. **The attention-ceiling connection does not transfer to Stage 1/3**, reasoned
   rather than re-measured —
   [spec/ATTENTION_CEILING.md](ATTENTION_CEILING.md#does-the-ceiling-reach-stage-1-and-stage-3-2026-09-02-reasoned-not-measured).
3. **Universal candidates are GitHub Issues, never a `candidates/` file** —
   [spec/SOURCES.md](SOURCES.md#universal-candidates-are-github-issues-not-a-fourth-candidates).

## Stage 4's actual scope, stated plainly

The plan's own approval table names three routes. Only one of them needed
new code:

- **Individual** — the owner's own `--approved-by NAME` on
  `precedent_land.py` *is* the approval, per the plan's own text. No pull
  request (PR), no review.
- **Team** — `approvers.json` and its generated `CODEOWNERS` **already
  existed** in `precedent-team-maintainers` before this phase started (a
  private-repo reconcile session built it, independently, to satisfy the
  plan's own stated requirement ahead of phase 5 actually needing it).
  `precedent_land.py` verifies the named approver against that file before
  landing directly — the plan's own explicitly-sanctioned collapsed path
  for a small team ("the session commits it directly"), which is what this
  real two-person team (`themorgan`, `alex137`) actually uses. **The
  non-collapsed path — a real proposal branch and pull request, reviewed by
  an approver before landing — is not automated.** Opening that pull request
  by hand (draft the file with `precedent_promote.py`'s output, commit it to
  a branch, push, open the request) works today; automating it needs a
  GitHub credential for the team's own repo, the same deferred gap named
  below.
- **Universal** — `precedent_land.py --level universal` drafts
  `practices/<slug>.md` in the working tree and stops. A pull request is
  still the actual approval; this tool cannot grant it.

## What is deferred, not missing

Both traceable to the plan's own [Per-repo credentials](../PRACTICE_ENGINE_PLAN.md#deferred-speculative--do-not-build-yet)
entry ("failing gracefully and reporting the gap. Real, but not day one"):

- `precedent_candidate.py create --level universal` drafts a GitHub Issue
  body; it does not open the Issue. `--out FILE` or stdout, then paste it at
  the URL the tool prints.
- The team-level non-collapsed pull-request path above.

Neither is a script gap that could be closed by writing more Python — both
need a GitHub credential scoped to a repo this tool suite does not assume
it has, for a team or a universal maintainer this session cannot know in
advance. A session with its own GitHub access (this one, for instance) can
do either step by hand in the meantime.

## What Stage 6 can and cannot measure, and why that is stated rather than hidden

`tools/precedent_retire.py` flags a practice only on **two** signals it can
actually verify — never cited elsewhere in the tree, and unreachable by any
channel (the same three-way test `check_reachability` already applies,
plus resident tier). **"Whose check never trips" is not measured at all**:
nothing in this codebase logs check-run history across time, only the
current run's pass/fail, so a claim about historical trip frequency would
be invented, not computed. This is the same discipline
`routing_eval.py --enforcement` already applies to a different question
("coverage, not compliance") — say what the number is not evidence of,
rather than let it be read as more than it measured.

## What phase 6 inherits

- **The pipeline is real and tested, but has never processed a real
  candidate.** Every case run against it so far is a fixture (throwaway
  repos, invented slugs) or a smoke test cleaned up immediately after. The
  first real candidate raised against a real incident is still ahead, and
  will be the actual test of whether the four criteria are calibrated
  right — this phase measured that the machinery works, not that its
  thresholds (2 for recurrence, 50% for duplication overlap) are the right
  ones. Revisit both if the first several real candidates feel wrong.
- **The `for_team:`/`in_repos:` individual-practice scoping field is
  designed, not built** —
  [PRACTICE_ENGINE_PLAN.md's Deferred section](../PRACTICE_ENGINE_PLAN.md#deferred-speculative--do-not-build-yet)
  carries the frontmatter shape and the resolver's conflict rule. Build it
  when a second team makes `for_team:` testable against a real conflicting
  pair, per that entry's own reasoning.
- **The pre-fork catalogue audit table** (verdict per inherited practice
  against this plan's architecture) that
  [What phase 5 should carry forward](../PRACTICE_ENGINE_PLAN.md#what-phase-5-should-carry-forward)
  named is still not done. It is not phase-5-blocking (the plan only
  requires it before phase 6), but phase 6 should not start migrating a
  consumer repo without it — this phase ran out of scope to do both the
  pipeline and the audit.
- **`repeated-check-failure` has no detector**, named as a real gap in
  `precedent_detect.py`'s own header rather than a silent omission. Building
  one needs a persistent log of check runs this codebase does not keep
  anywhere yet — a bigger piece of infrastructure than this phase's own
  scope, and arguably its own candidate.

## Two real bugs this phase's own harness work found

Worth naming because both were found by writing a check and watching it
fail on real content, the discipline `checkable-gets-checked` names
directly, not by reasoning about the code in the abstract:

- `precedent_retire.py`'s first draft compared frontmatter values (raw
  strings — `applies_to` reads back as the literal text `'["**"]'`, not a
  parsed list) against parsed-type literals, so its reachability test never
  actually fired on anything. Caught by planting a genuinely dormant
  fixture practice and watching the report stay silent — fixed to compare
  against the same string literals `verify_harness.py`'s own
  `check_reachability` already established.
- `check_decision_records_not_inline`'s entry-matching regex ran over the
  *whole* plan document, not just the "Amendments Since Approval" section
  it was built to measure. A design edit in this phase's own Deferred
  section (the `for_team:` field) landed inside an unbounded tail-span
  running from an old 2026-08-31 amendment through two later sections,
  because nothing in between happened to open a line with a bold date —
  and got reported as an 800-word amendment violation. Scoped the check to
  the section between its own heading and the next `## `.

## For the session that deep-checks this before Phase 6

Written for the session Morgan opens next, whose job is to test this phase
against real work rather than fixtures, and close whatever it finds before
Phase 6 (consumer-repo migration) starts on top of it. **Read
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) in full before
touching anything** — "How a Practice Comes Into Existence" (Stages 1–6),
the Sequence table's phase-5 row, and v30 of "Amendments Since Approval" —
and this whole brief, not just this section. Confirm your local checkouts
of all three repos are current before doing anything else
(`git fetch origin <branch>` on each — `AGENTS.md`'s gotchas section has the
story of what a stale checkout looks like and why it gives no error).

### The pipeline has never touched a real candidate — that is the actual gap

Every case run against it so far is a fixture built inside a throwaway
directory, or a smoke test cleaned up in the same breath it was created.
The mechanism is proven; the four criteria's specific numbers (recurrence
≥ 2, > 50% word-overlap for duplication, the 2,000-token resident cap) are
not calibrated against anything real. **Raise a genuine candidate from a
genuine incident** — this session's own work is full of candidates
(a corrected assumption, a repeated instruction, a real cost from getting
something wrong) — and run it through `precedent_promote.py` and
`precedent_land.py` for real, at least once each for individual and team
level. If a real case makes a threshold feel wrong, that is exactly the
signal Stage 3 exists to produce; change it and say why, the same way this
phase changed `routing_scope.json`'s globs on evidence rather than by
precedent.

**Also exercise the two paths this phase deliberately left manual**,
at least once, so they are proven rather than only described:
- File a real universal candidate as a GitHub Issue using
  [.github/ISSUE_TEMPLATE/practice-candidate.md](../.github/ISSUE_TEMPLATE/practice-candidate.md) —
  confirm the template actually renders sensibly and the fields map cleanly
  onto what `precedent_promote.py` needs.
- Open one real team-level proposal as an actual branch and pull request
  reviewed by an approver, rather than the collapsed direct-`--approved-by`
  path — the collapsed path is tested; the path Stage 4 describes as the
  normal case for a larger team is not.

### A known bug, found while writing this brief — fixed by the deep-check session (2026-09-02)

`precedent_candidate.py create`'s file name was `<slug>-<date>.md`, and
`cmd_create` refused outright if that exact file already existed. Raising
the same candidate twice on the same calendar day used to fail with an
error, instead of registering as recurrence — the opposite of Stage 3's
own design ("a count of files, not a field a session has to remember to
increment," spec/CANDIDATE_FORMAT.md). **Fixed**: a same-day, same-slug
collision now suffixes a sequence number (`<slug>-<date>-2.md`, `-3.md`, …)
instead of refusing, with a planted harness case (two same-day raises of
one slug; confirm neither fails and `recurrence_count` reads correctly
afterward) in [tools/verify_harness.py](../tools/verify_harness.py)'s
`check_creation_pipeline_fires`.

### Other things worth adversarial pressure, not yet applied

- **`precedent_promote.py`'s non-duplication check only searches
  `--against`, which defaults to `[ROOT]` (BestPractice/universal alone)
  regardless of the candidate's own level.** Promoting a team candidate
  without explicitly passing `--against <team-path>,<universal-path>`
  silently never checks it against that team's own catalogue. Worth
  deciding whether the default should be smarter (derive it from `--level`
  and `--path`) or whether it is fine as an explicit, documented caller
  responsibility — but decide on purpose, not by never having noticed.
- **`precedent_candidate.py`'s frontmatter reader/writer (`_parse_frontmatter`,
  `_yaml_scalar`) is a hand-rolled, deliberately narrow parser for the
  frontmatter's restricted shape**, not a real parsing library for the
  underlying format. It has not been stress-tested against edge cases a real
  candidate might produce: a comma or a literal `]` inside a quoted list
  item, an observed-text or proposed-rule containing a line that looks like
  frontmatter, an embedded `---`. Throw a few adversarial candidates at it.
- **The word-overlap duplication heuristic** (`precedent_promote.py`'s
  `_word_set` / Jaccard-style ratio, also reused by
  `precedent_detect.py restated`) has only been checked against one
  deliberately-exact collision (`verify-postcondition` vs. itself) and one
  deliberately-unrelated pair. Run `precedent_detect.py restated` for real
  across all three sources together (this phase only ever ran it
  individual-vs-team) and sanity-check a few of its actual near-duplicate
  claims by eye — a heuristic with no adversarial pressure yet is a
  heuristic that has not really been tested.
- **The leak gate's vocabulary layer was switched on once, briefly, during
  this phase's own pre-flight check** (`PRECEDENT_LEAK_BLOCKLIST` pointed at
  `precedent-individual`'s real blocklist, `git config
  precedent.requireVocabulary true`) and immediately found 45 hits on
  already-committed, already-public content — `themorgan` and `Buenos
  Aires`, both named as non-sensitive in
  [decisions/2026-09-01-relax-private-repo-isolation.md](../decisions/2026-09-01-relax-private-repo-isolation.md)
  and both already appearing throughout this branch's own published spec
  docs. **This was reverted rather than fixed, and nobody has decided
  whether the blocklist is miscalibrated (too broad for what it actually
  guards) or whether the vocabulary layer has in fact never really run
  clean on this branch.** This is a real gate meant to protect against
  publishing something sensitive into a public repo, currently sitting
  unusable in practice — worth Morgan's own judgment call before Phase 6
  widens who else's content this branch might ever touch, not something to
  leave discovered-and-dropped a second time.
- **Re-run the full deep-check suite fresh** on all three repos
  (`verify_harness.py`, `doc_lint.py`, `leak_gate.py`, `precedent_check.py`,
  `doc_sync.py` on BestPractice; `tools/checks/tests/run_all.sh` on each
  private repo) before starting anything new — this phase's own harness
  work found two real, unrelated bugs (above) just from being written and
  run, which is exactly the case for not assuming last session's green run
  is still green.

### Still open from this phase, restated so it is not missed

- **The pre-fork catalogue audit table** (verdict per inherited practice
  against this plan's architecture, one row each) that
  [What phase 5 should carry forward](../PRACTICE_ENGINE_PLAN.md#what-phase-5-should-carry-forward)
  named — not done. The plan only requires it before Phase 6, which makes
  this the session to do it, not a future one.
- **`for_team:`/`in_repos:` is designed, not built** — see the plan's own
  Deferred section. Still correctly not built (no second team exists yet
  to test `for_team:` against), but worth a fresh look in case that has
  changed.
- **`repeated-check-failure` has no detector** and needs a persistent
  check-run log this codebase doesn't keep — a real gap, plausibly its own
  candidate rather than something to build reflexively here.

### Testing this for real: upgrading a forked consumer repo

**Do this last** — after the fixture pipeline has been raised against real
candidates, the manual paths have been exercised, and the bugs and gaps
above have had a real look, not before. This is the biggest and least
certain piece of work in this brief, and everything above it is cheaper to
get right first.

Morgan's own request, and the single most valuable thing this session can
do: **no repo has ever actually been migrated onto Precedent.** Phase 6 is
where that is supposed to happen for real, but nobody has rehearsed it even
once, and `INSTALL.md` still documents BestPractice's *old*, pre-fork
vendoring model (`process/upstream/`, adaptive templates, a manifest) —
correct for a project still on `main`, silent on what changes for a
project that wants `precedent-beta-v01` instead. Doing this as a real,
disposable dry run — on a **fork**, not the real repo, so nothing here
touches Morgan's actual work — is exactly how phase 2's own premise got
tested instead of assumed, and it should produce the same kind of thing:
a written account of what held and what didn't, not a clean success story
polished after the fact.

**State this plainly going in, so it isn't mistaken for a mistake partway
through: this is genuinely unrehearsed ground.** The steps below are this
session's best reasoning from what actually exists (`precedent_resolve.py`,
`precedent.json`, `ADOPTING.md`'s vendoring guidance, the individual-set
bootstrap pattern already built and validated), not a procedure anyone has
run before. Expect at least one real gap — one is named below, found while
writing this brief, not by running the steps — and treat finding more of
them as the point of doing this, not as this brief having been wrong.

**0. Set up the fork, isolated from anything real.**
**Confirm the real target repo's name before forking anything** — an
earlier draft of this step named `WritingWithAI`, but
`precedent-individual`'s own `leak-blocklist.txt` names a
different-looking private project for what may be the same repo, and
nobody has confirmed the two are actually the same (see
[spec/PHASE5_DEEPCHECK.md](PHASE5_DEEPCHECK.md)'s "Notes for the next
session" for how this was found). Read that blocklist, or ask Morgan
directly, rather than trusting either name on its own. Once confirmed,
fork the real repo on GitHub (a real fork, so it is a separate repo with
its own default branch — not a branch of the original), and `add_repo` it
to this session with push access. Everything from here on happens only in
that fork.

**1. Point the universal source at `precedent-beta-v01`, not `main` —
the actual question Morgan asked.** `precedent.json`'s `path` for a source
is read straight off the filesystem
(`tools/precedent_resolve.py`'s `load_source`); nothing about it knows or
cares which branch of BestPractice a checkout is on. So "point at
`precedent-beta-v01`" only means: whatever directory that path names must
itself be checked out to that branch. Two ways to satisfy that, and for a
repo more than one person will ever work in, only the first one actually
works:

   - **Vendor it** (the model `ADOPTING.md` describes: "copy Precedent's
     practice library into your project, as ordinary files"). Clone
     BestPractice at `precedent-beta-v01`, copy its `practices/` tree into
     the fork at a tracked path of your choosing (e.g. `precedent/universal/`),
     and record the exact commit copied from — the same discipline
     `precedent-team-maintainers/practices/install.md` already names for
     the old vendoring model ("record the source repo and the commit it
     was installed from, so a later sync has something real to compare
     against"), ported to this branch rather than `main`. This is committed,
     ordinary, git-tracked content: every contributor and every fresh
     container gets it for free, with nothing to clone at session start.
   - **Point at a local sibling clone** (what this session's own dev
     environment does, and what a synthetic test fixture like
     `check_source_precedence`'s does) — `precedent.json`'s `path` names an
     absolute path to a `precedent-beta-v01` checkout that happens to exist
     on this machine. Fine for a quick, throwaway, single-container
     experiment; wrong for anything committed, since the path is
     meaningless the moment anyone else opens the fork, or this same
     container restarts.

   **Vendor it, for this test** — the point is rehearsing what a real
   migration looks like, and a real migration vendors.

**2. Vendor the team source the same way**, from
`precedent-team-maintainers`'s own `practices/`, and **wire the individual
source using the pattern that's already built and already validated** —
[`precedent-individual`'s own `claude-web-bootstrap.md`](https://github.com/themorgan/precedent-individual/blob/main/practices/claude-web-bootstrap.md)
names the exact two files to copy in
(`bootstrap/session-start.sh` → `.claude/hooks/`,
`bootstrap/settings.snippet.json` merged into `.claude/settings.json`) and
says this was "validated end-to-end 2026-08-31." Use it rather than
re-deriving it.

**3. Vendor each source's own `tools/checks/` alongside its `practices/`,
not just the Rules.** A practice that claims a `checked_by` pointing at
`tools/checks/check_<name>.py` has nothing behind that claim if only
`practices/` was copied — the check scripts are what makes the claim real
(`engine-plus-host-shims`: the engine travels with what it enforces, not
separately).

**4. Write the fork's own `precedent.json`** naming the universal and team
sources at their vendored paths, then run
`python3 tools/precedent_resolve.py --repo <fork>` (from a BestPractice
checkout, pointed at the fork) to confirm: all three sources resolve, the
precedence and `overrides:` behavior looks right against real content
instead of fixtures, and — the thing this whole mechanism was built to
prevent silently — the combined resident block is reported and stays
under the 2,000-token cap. This step is real and immediately testable with
tooling that already exists and is already tested; expect it to work.

**5. Here is the gap this brief can name in advance, found while writing
it rather than by running these steps.** `precedent_resolve.py` is the
*only* multi-source-aware tool in this codebase.
`tools/build_views.py` (`AGENTS.md`'s generated loader block, MAP.md,
GLOSSARY.md), `tools/precedent_paths.py` (the path-triggered channel),
`tools/precedent_gate.py` (the gate-triggered channel), and
`tools/precedent_check.py` (the enforced channel) **all read a single
local `practices/` directory relative to wherever they're run** —
none of them accept multiple source directories the way
`precedent_resolve.py` does. So step 4 proves the *resolver* works; it
does not, by itself, give the fork a working generated `AGENTS.md`, a
working occasion index, or a working enforced channel that reflects all
three sources together. **You will need to bridge this to get a real
working session out of the fork**, and how to bridge it is genuinely open
— two shapes worth trying, in order of how much they cost:
   - **Materialize a merged tree.** A short script that calls
     `precedent_resolve.py`'s own `resolve()` and writes each winning
     practice's file into one local `practices/`-shaped directory, then
     points `build_views.py`/`precedent_paths.py`/`precedent_gate.py`/
     `precedent_check.py` at that directory unchanged. Fastest to try; the
     honest cost is that the materialized tree is a derived artifact that
     needs regenerating on every source update, which is exactly the kind
     of drift `generated-artifact-provenance` exists to keep visible
     rather than silent.
   - **Extend the single-tree tools to accept multiple source directories**,
     the way `precedent_resolve.py` already does — the more correct fix,
     and a real chunk of engine work, not a one-off script.

   Don't try to build the permanent version of either mid-test. Do
   whichever unblocks the experiment fastest, note which one you did and
   why, and write up what the real fix should look like — that write-up
   is worth more to Phase 6 than the workaround itself, and if it turns
   into real, reusable engine code, it belongs in `tools/` here, proposed
   and merged onto `precedent-beta-v01` like anything else in this phase.

**6. Once the fork has a working loader, do real work in it** — anything
genuine, not a staged demonstration — with an assistant reading whatever
`AGENTS.md` step 5 produced. Watch for what phase 2–4 already learned to
watch for: does the resident block actually get used, does the occasion
index get consulted for the things it names, do `checked_by` scripts
actually fire when they should. **Raise at least one real candidate from
something this work surfaces** — the same "genuine incident" opportunity
this brief opened with, above, and doing it inside a real migration is a
better test than doing it in isolation.

**7. Write up what happened**, plainly, the way this document's own "Two
real bugs" section does — what matched the plan, what didn't, what step 5
actually needed, and what `INSTALL.md` (or a new phase-6 document) should
say for the next repo that does this for real. This write-up, not a clean
migration, is the actual deliverable of this test.
