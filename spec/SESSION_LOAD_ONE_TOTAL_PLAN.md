---
title:         One total per session instead of a budget per part
kind:          proposal
status:        accepted
opened:        2026-10-28
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Token-budget blocks came back on 2026-10-27/28 because tokens moved between budgets, not because sessions got heavier. Proposal, revised after an independent review: one refusing number, the total a session loads from its generated files, declared once by the person and copied into each repository so CI sees it; the per-part numbers stop being stored or approved."
---

# One total per session instead of a budget per part

**Status: accepted.** Morgan, 2026-10-28 (strength: decided): "Go, one
number everywhere". Revised after review before the go.
Measured 2026-10-28 on the `main` branches of BestPractice and the three
private sources this session had attached. An independent session reviewed
the first draft the same day; what it found and what changed is in
[Review](#review).

## What happened

In September every change seemed to need a budget raised somewhere. The
fixes then were: a cap on the occasion index (2026-09-14), a share of it per
source with a consumer's cap derived from the sum (2026-09-29), a registry
of the person's approved maximums (2026-09-30), a budget of the person's own
for the sets they bring (2026-10-03) and one for their individual set
(2026-10-20). That stopped the asks for about three weeks.

They came back on 2026-10-27 and 2026-10-28. Three events, none of which
made a session meaningfully heavier:

1. **Rules moved between sets.** On 2026-10-19 thirteen rules moved from the
   individual set to the ladder set. The ladder set's occasion share was
   raised 550 to 750 and the individual set's lowered 600 to 400 the same
   day, with Morgan's yes. But a consuming repository pays for the ladder
   set out of a *third* budget, `brought_sets_tokens`, and nothing moved
   that one. On 2026-10-27 a consumer's full check failed at about 1,330
   against 1,100, and the budget was raised to 1,400 on "raise it".
2. **Sets copied into repositories.** Copying a shared set into the
   repository that uses it (spec [VENDORED_SHARED_SETS.md](VENDORED_SHARED_SETS.md))
   rolled out through Update Vendors over these two days. A copied set stops
   being paid from the person's brought budget and starts being paid from
   the repository's occasion cap and session-file ceiling. Every repository
   that copied a set in then failed `budget-within-approval` in turn. Two
   engine commits on 2026-10-28 (`953254be`, `64d0b49b`) now record the
   approval automatically when the rise is within the copied sets' shares.
3. **An accounting fix.** Commit `9936acc9` (2026-10-28) counted the moved
   rules under the brought set instead of the individual set. Measured in
   BestPractice, brought went 413 to 812 and individual 1,103 to 704 (the
   commit's own figures; individual measured about 656 later the same day).
   The total did not change. A session predicted the brought budget would need
   about 1,800 and prepared to ask; the consumer measured about 1,134 and no
   raise was needed that time.

So the guess that the copy-in of the ladder and writing sets is behind it
was right for event 2, and event 1 is the same thing one step earlier:
rules changing which set carries them.

## Why it keeps coming back

**The budgets are attached to the accounting, not to what a session pays.**
A session in a consuming repository loads one AGENTS.md, one CLAUDE.md and
one session-start file. What it pays is their sum. But that sum is cut into
pots, each with its own number, each set as a tight watermark (measured
size plus 10-20%), and each raisable only by Morgan:

| Where | Budgets in force |
|---|---|
| Each source (four here) | occasion share, resident cap, and its own AGENTS.md, CLAUDE.md and session-file ceilings |
| The individual set, for the person | `individual_set_tokens`, `brought_sets_tokens` |
| Each consuming repository | AGENTS.md, CLAUDE.md and session-file ceilings, resident cap, occasion cap |

The four source repositories alone carry 26 entries in `approved_budgets`;
every consuming repository adds about six more.

**Any change to the structure moves tokens from one pot to another**: a rule
moving between sets, a set copied in, a set added to or dropped from
`brings`, a fix to how a share is counted. The total stays where it was, the
receiving pot overflows, and a session stops to ask for words only Morgan
can give. The project changes its structure every week, so this will keep
happening.

**Each past fix closed one route and left the pattern.** The derived
occasion cap, the brought budget, the individual budget and today's
copy-in auto-approval each handle one way tokens move. The next new way (a
rule moving from universal into a shared set, say, or a set leaving
`brings` for a repository's own declaration) asks again.

**And the budgets that pay for one set are literals that repeat each
other.** On 2026-09-29 Morgan decided "give each practice set its own
allowance ... and set each repo's cap to the sum of the allowances for the
sets it uses" (strength: decided). `brought_sets_tokens` (2026-10-03) and
`individual_set_tokens` (2026-10-20) are hand-set totals beside those
per-set allowances, not sums of them. Event 1 is that duplicate failing to
follow a share move Morgan had already approved.

**Meanwhile per-turn and hook text is in no budget.** The session-start
hook adds a list of spoken commands and source-resolution notes on top of
the session file, and the reply gate's list is injected again on every
turn. Both vary with the session's state, so neither is a stable thing to
cap (see [Review](#review)).

**The next two blocks are already visible.** The ladder set's occasion share
is at 695 of 750 (93%) and its AGENTS.md at 1,352 of 1,400 (97%). The next
rule added to that set refuses.

## Options considered

### A. Keep the pots, and write an offset for every route

When a rule moves between sets, move its tokens between the budgets that
pay for it; when a set is copied in, move its share from brought to the
repository (done for that one route on 2026-10-28, `953254be` and
`64d0b49b`).

**Holes.** The routes are open-ended, so this is the route-by-route
patching that has not held. The pots live in different repositories, so
one move has to write approvals in several at once. It leaves every pot as
tight as before. **Rejected.**

### B. Raise every pot with real headroom

**Holes.** It stops the asks for a while, but tokens moving between pots
still overflow the smaller ones. It is the band-aid. **Rejected.**

### C. Remove the budgets

**Holes.** Before 2026-09-11 the occasion index grew about 160 tokens a day
with nobody deciding it. That comes straight back. **Rejected.**

### D. One total per session, parts as notices (the first draft)

One refusing number, the total a session loads including the session-start
hook's output, declared once in the person's individual set; every part's
number kept as a non-refusing notice.

**Holes the review found** (all checked against the code):

- **CI cannot see the person's number.** The daily and post-merge checks
  run with only the workflow's own token and cannot read the individual
  set. With no total resolvable there, every per-part check would still
  refuse in CI, so the asks come back through the "merge and get notified"
  route.
- **Hook output is the wrong thing to measure.** It changes with the
  session's state (a source that fails to resolve adds a block), so a
  broken environment would raise the total and refuse a push. Measuring it
  means running hooks that fetch and write, which a check cannot do. And
  large hook output is truncated before the model sees it.
- **Parts kept as notices go stale.** Nobody raises them any more, so they
  sit under what they measure and their notice fires every session until it
  is ignored.
- **The effort was underestimated** (about three to four hours stated).

### E. One total over the generated files, nothing else stored (proposed)

D's direction, with each hole closed. Described in full below.

## The proposal

**One number refuses: the total a session in a given repository loads from
its generated files** -- AGENTS.md, CLAUDE.md, the session-start practices file
the private sources write, and the generated spoken-command list. Each is rendered deterministically,
so the same tree measures the same everywhere. Hook extras and the per-turn
gate list are reported as a notice, never refused.

**The person declares it once** (`session_load_tokens` in their individual
set), and **Update Vendors writes it into each repository's own registry**
with the approval words, the way `953254be` records a copy-in's occasion
cap. CI, other people's checkouts and Morgan's sessions then read the same
number, and the same tree passes or fails the same for all of them.

**Nothing else is stored or approved.** `brought_sets_tokens` and
`individual_set_tokens` are deleted: what the sets cost is measured, not
declared. The per-set allowances, the resident caps and each surface's
ceiling stop refusing where a total is in force. In their place the merge
and push gates print **which part this change grew, and by how much** --
computed from the change, so there is no stored number to go stale. A
repository with no total keeps today's behaviour, so other people's
installs are untouched.

**Moving a rule, copying a set in, or fixing how a share is counted never
asks**, because none changes the total. The 2026-10-28 copy-in approval
code becomes unneeded and is removed.

### Where refusals happen, before and after

| Check | Today | With a total in force |
|---|---|---|
| `budget-within-approval` | refuses at every tier, for every part | refuses only when the total is above its approved max |
| `session-load-budget` | warns at the quick check, refuses at the full one | refuses the total at the full check; warns at the quick one |
| `loader-within-caps`, `session-file-allowances-fit` | warn quick, refuse full | report only |
| [build_views.py](../tools/build_views.py) occasion and resident caps | warn, or fail with strict budgets | report only |
| Session check's brought and individual rows | a failing row at session start | removed; the total's row replaces them |

### What it gives up

**It reverses Morgan's decision of 2026-09-14** (option D, strength:
decided): the occasion cap was set "deliberately tight ... meant to be met
soon and often", so each new index line forced a decision. Under this
plan, index lines no longer ask. The per-change growth line still shows
each one.

**One person-wide total is loose for the smaller repositories.** Measured
2026-10-28 from the generated files, the session-start file counted in
full: BestPractice about 8,100 tokens, the three practice-set repositories
about 5,900 to 6,300. A single number sized for BestPractice gives a
smaller repository well over half again its load before anything
refuses. Two ways to choose, for Morgan:

- **One number everywhere.** Simplest; the headroom notice (within the registry's
  `headroom_floor_pct` of the total) and the per-change
  growth line are the only brakes in a smaller repository.
- **One number per kind of repository** (a source set, BestPractice, a
  project). Tighter, at the cost of a few numbers instead of one.

The go comes with each repository's measured load beside the number
proposed, so the slack is visible when he picks.

### Build order

1. **Engine (BestPractice):** the total over the generated files; its
   approval in `budget-within-approval`; the refusal table above; the
   per-change growth line; Update Vendors writing the total into each
   registry; tests for both paths and one that moves a rule between two
   sets and asserts nothing refuses.
2. **Remove what it replaces:** the brought and individual literals and
   their session-check rows, the copy-in approval code, the per-part
   rows in `very_deep_check.budget_rows`.
3. **Practice text:** [session-load-budget](../practices/session-load-budget.md)
   and [reduction-pass](../practices/reduction-pass.md).
4. **Morgan's number** in the individual set, then Update Vendors across his
   repositories.

**Effort:** about a day of session work for steps 1-3, then the Update
Vendors run. Step 1 alone closes the asks on every route; steps 2 and 3 can
land after it.

## Review

An independent session (Opus, read-only) reviewed the first draft on
2026-10-28 and recommended adopting it with seven changes. Each is taken:

1. **CI could not see the total** -> Update Vendors writes it into each
   repository's registry (checked: the daily workflow runs with only its
   own token).
2. **Hook output is unstable to measure** -> the total covers the
   generated files only; hook extras and the gate list are a notice.
3. **The brought and individual literals duplicate the per-set allowances**
   against the 2026-09-29 rule -> deleted; named as part of the cause.
4. **Parts as notices go stale** -> no per-part numbers stored; a
   per-change growth line instead.
5. **No list of refusal sites by tier** -> the table above (checked: the
   size checks already only warn at the quick check).
6. **The 2026-09-14 decision is reversed, and should be said so** -> said,
   with the loose-total trade and a choice for Morgan.
7. **Effort and two figures** -> re-estimated at about a day. The draft's
   "about 1,500 unbudgeted hook tokens" was one session's measurement and
   varies with session state, so it is dropped; the 704 is the commit's own
   figure, now marked as such.

The reviewer also proposed deriving one share per set and keeping
approvals per set. This plan goes one step further and stores no per-set
numbers at all: a share that refuses nothing and needs no approval is a
measurement, and the growth line already reports it.
