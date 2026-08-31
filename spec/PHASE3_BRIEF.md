<!-- Last updated: 2026-08-31 (Buenos Aires) by the phase-3 build session -->

# Phase 3 Brief — Split the Sources

**Status: phase 3 is done on Precedent's side.** This is kept as the record
of what phase 3 was handed, not as a live work list. What phase 3 actually
built, what it deliberately did not, and what remains open are in
[spec/SOURCES.md](SOURCES.md) and in the plan's
[What Phase 3 Built, and What It Could Not](../PRACTICE_ENGINE_PLAN.md#what-phase-3-built-and-what-it-could-not).
The short version: items 2–6 below are done; **item 1 — populating the two
private sets from RepoPersonalPreferences' 46 rules — is not, and cannot be
done by a session working in Precedent.** A session cannot hold repositories
from two owners with push access at once, and the plan forbids staging
private content on this branch even transiently. That work belongs to a
session opened against those repositories. See
[What phase 4 inherits](#what-phase-4-inherits) at the end.

Written for the session that does phase 3, by the session that closed phase
2. Read [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) first — this
brief is what phase 2 learned that the plan could not have known, plus the
state of the tree you are inheriting. It is not a substitute for the plan.

## Where things stand

Phases 0, 1, 1.5 and 2 are done and pushed to `precedent-beta-v01`. `main`
is untouched at `88ecf7f` and **stays untouched** — nothing merges to `main`
until the whole rewrite is complete (phase 7).

| | state |
|---|---|
| Practices | 52 files in [practices/](../practices), Rule/Why/Story/Install, 19 with a real Story |
| Loader | resident block (6 practices, ≈621 of a 2,000-token cap), occasion index (46 authored clauses), path-triggered channel |
| Generated views | [AGENTS.md](../AGENTS.md)'s loader block, [MAP.md](../MAP.md), [GLOSSARY.md](../GLOSSARY.md) — hand-editing any of them fails a check |
| Harness | [tools/verify_harness.py](../tools/verify_harness.py), 20 checks passing, 1 N/A |
| Leak gate | [tools/leak_gate.py](../tools/leak_gate.py) — structural layer live and gating every push and every branch in CI; **vocabulary layer is yours to switch on** |
| Enforcement | 8 of 52 practices carry a `checked_by`, naming 4 distinct scripts |

## What phase 3 owes, per the plan's Sequence row

1. **The private sets exist but are empty.** `themorgan/precedent-individual`
   and `themorgan/precedent-team-maintainers` are created. Populate them from
   RepoPersonalPreferences' 46 rules, per the plan's
   [Where Today's Practices Go](../PRACTICE_ENGINE_PLAN.md#where-todays-practices-go):
   default everything to **team**, promote to universal only individually,
   and move the Morgan-specific handful to individual. Two RPP rules
   (`morgan-scope`, `bestpractice-wins`) **die rather than move** — the
   structure now says what they said.
2. **Switch the leak gate's vocabulary layer on.** Write the private-term
   blocklist **into the individual set**, and point
   `PRECEDENT_LEAK_BLOCKLIST` at it. Run
   `python3 tools/leak_gate.py --explain` before you do anything else here.
3. **Split `## Detail` out of `## Rule`** across the catalogue — see below.
4. **The frozen example set** — a one-time illustrative copy of the
   individual set, never updated from it.
5. **The adopter README**, drafted in prose, for someone who has never seen
   Precedent and is not a developer.
6. **A consumer repo resolves all three sources, and precedence is tested.**

## Five things phase 2 learned that change how you should do phase 3

**1. Every push is publication, and the leak gate's second half is missing.**
Precedent is a branch of a public repo owned by someone else. There is no
"private initially" grace period and nothing to force-push away. The
structural layer runs already; the vocabulary layer — the one that catches
private *words* — does not, because its blocklist cannot live in this repo
(a list of secret terms in a public repo publishes the terms). **Do this
before any private-set content comes near this working tree**, not after.

**2. Do not stage private content here, even transiently.** Levels are
repositories. Build the private sets in their own repos and wire Precedent to
*resolve* them. The leak gate refuses individual/team-shaped paths by design;
if you find yourself wanting to disable a rule to make progress, that is the
rule working.

**3. The `## Detail` split is cheap — use the machinery, do not hand-edit.**
[tools/resplit_sections.py](../tools/resplit_sections.py) moves text **by
reference**, from decisions recorded as data in
[tools/section_split.json](../tools/section_split.json). Retyping a sentence
is not something the mechanism can do. Add a `"detail"` key alongside
`"rule"`, extend `SECTIONS`, and the content-preservation checks
(sentence-for-sentence against `PRACTICES.md`, source order, list structure)
already guard it. Twenty practices have Rules over 150 words; that list is
your work queue. Two constraints from the plan: **`## Rule` must stay
loadable on its own** — a session reading only the Rule must know what to
*do*, not merely that something applies — and **`## Detail` must come from
the same `precedent show` command**, not a second one.

**4. The loader is a cost optimisation, not a compliance mechanism.** Phase 2
measured it: 62% less context for 19 points *worse* recall than carrying
everything, and both arrangements miss the same practices. Read
[What Phase 2 Measured](../PRACTICE_ENGINE_PLAN.md#what-phase-2-measured)
in full before you make any claim about what the loader buys. In particular,
**do not tune the occasion index to chase the recall number** — the ceiling
is not in the routing layer.

**5. Write the adopter README against the measured claim, not the hoped-for
one.** It is the first thing anyone outside this project will judge, and the
honest pitch is stronger than the original: *your team's habits get captured
and then enforced*, with the loading layer as what keeps the cost flat. The
plan's own [constraints on how it is written](../PRACTICE_ENGINE_PLAN.md#precedent-needs-a-readme-for-people-adopting-it)
still hold: no internal vocabulary, and assume the reader is not a developer.

## How to work in this tree

- **Branch `precedent-beta-v01` only.** Never `main`. Use the same commit
  identity the branch already uses — take it from `git log -1 --format='%an <%ae>'`
  rather than from a note here, which is both more reliable and keeps a
  personal address out of a public file (the leak gate flags one, correctly,
  and flagged an earlier draft of this very brief). Timestamps in Buenos
  Aires: `TZ="America/Argentina/Buenos_Aires" git commit ...`. Never amend a
  pushed commit.
- **Run all three gates after every change**, not just at the end:
  `python3 tools/verify_harness.py` (expect 20 passed / 0 failed / 1 N/A),
  `python3 tools/doc_lint.py`, `python3 tools/leak_gate.py`.
- **Never read a `practices/*.md` file directly.** Use
  `python3 tools/precedent_show.py SLUG [--why|--story|--install]`, and
  `python3 tools/precedent_paths.py FILE` for what applies to a file.
- **The generated views are generated.** Hand-editing AGENTS.md's loader
  block, MAP.md or GLOSSARY.md fails a check. Run
  `python3 tools/build_views.py`.
- **A test that passes on a bug is worse than no test.** Phase 2's two worst
  defects — a converter deleting a practice's whole Install section, and a
  path matcher that never matched a top-level file — were both green across
  the entire harness, because in each case the check had been written against
  the same assumption as the thing it checked. When you add a check, break
  the thing it guards and watch it fail before you trust it.

## Do not start phase 4 or 5

Phase 4 is now the **enforcement push** (swapped ahead of the creation
pipeline by the phase-2 measurement). Its starting queue is already known —
the seven practices phase 2 measured as most-missed, every one of which
carries `checked_by: null`:

`cite-the-incident` · `capture-gate` · `verify-postcondition` ·
`environment-gotchas` · `engine-plus-host-shims` · `convention-to-audit` ·
`mistakes-become-rules`

`cite-the-incident` is the obvious first one and the reason to note this
here: now that practices are files with a `## Story` section, *"a new
practice must carry its originating incident"* is a single function in the
harness we already run. It is the most-missed practice in the catalogue and
the cheapest to enforce. **Leave it for phase 4** — but do not let the
phase-3 work make it harder.

## What phase 4 inherits

Phase 4 is the enforcement push. Its starting queue is unchanged from what is
written above, and three things phase 3 changed underneath it are worth
knowing before it runs:

- **The eval was re-baselined, so start from the v3 queue, not the one above.**
  The split changed every arm's input, so the routing eval was re-run on the
  same 20 cases before phase 4 — otherwise phase 4's own result would have
  been confounded with it. Numbers and method in
  [spec/LOADER.md](LOADER.md)'s v3 section. The queue that matters now:

  | missed | caught | practice | reachable via |
  |---|---|---|---|
  | 8 | 2 | `practice-export-loop` | glob + **`checked_by`** |
  | 5 | 7 | `mistakes-become-rules` | occasion prose only |
  | 3 | 0 | `verify-postcondition` | **resident** |
  | 3 | 0 | `engine-plus-host-shims` | occasion prose only |
  | 2 | 0 | `environment-gotchas` | **resident** |
  | 2 | 0 | `docs-track-models` | glob + **`checked_by`** |

- **One entry breaks phase 4's framing.** `practice-export-loop` is the
  largest single miss and already carries a narrow `applies_to` *and* a
  `checked_by` — its glob fires only on `process/upstream/**` and these cases
  touch other paths. "Every most-missed practice carries `checked_by: null`",
  the observation that moved enforcement ahead of the creation pipeline, is no
  longer true of the most-missed practice. **Reach and enforcement are two
  problems.** Converting a practice to a check does not route it.
- **`verify-postcondition`'s Rule is now shorter, and the risk landed.** Its
  two concrete traps moved into `## Detail`. In v2 both arms missed it; in v3
  the control catches it 3 of 3 and the loader 0 of 3. Three cases cannot
  resolve why, and it is not on its own an argument to revert — v2 measured
  the long resident Rule and the loader missed it there too, 0 of 2. No run
  yet shows residency working for this practice at any Rule length, which is
  the argument for giving it a check.
- **`cite-the-incident` and `convention-to-audit` have left the queue** —
  1 miss of 15 applicable and 0 of 7 respectively, against 3 and 2 in v2. If
  you were going to start with `cite-the-incident` because it is cheapest,
  that is still a fine reason; it is no longer because it is most-missed.
- **Five practices' Rules could not be split** — `permutation-frontier-column`,
  `verify-decomposition`, `mistakes-become-rules`, `scripts-assert-properties`,
  `build-buy-decompose`. `mistakes-become-rules` is on phase 4's queue, and
  its length is the reason it is still 228 words: the proportionality guard
  that gates whether it fires at all cannot leave the Rule without changing
  what the practice does. If it gains a `checked_by`, the check has to carry
  that gate, not just the encode-the-prevention half. Two of the five were
  reverted after a review pass caught splits that every check had passed —
  see [spec/PRACTICE_FORMAT.md](PRACTICE_FORMAT.md).

One thing phase 3 added that phase 4 should use rather than rebuild: the
harness now has two worked examples of a check that tests a **behaviour** by
planting cases in a throwaway repository and asserting the exit status
(`check_leak_gate_fires`, `check_source_precedence`), rather than running the
thing and reporting what it says. Every practice converted to a
`checked_by` needs a test proving its check fires — the plan is explicit that
a `checked_by` without one is not finished — and that is the shape it should
take.
