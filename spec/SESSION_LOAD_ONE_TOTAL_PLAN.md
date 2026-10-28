---
title:         One total per session instead of a budget per part
kind:          plan
status:        proposed
opened:        2026-10-28
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Token-budget blocks came back on 2026-10-27/28 because tokens moved between budgets, not because sessions got heavier. Proposal: one refusing number per session, the total it loads, declared once by the person; every part's cap becomes a notice."
---

# One total per session instead of a budget per part

**Status: proposed, waiting on Morgan's go.** Measured 2026-10-28 on the
`main` branches of BestPractice and the three private sources this session
had attached.

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
   BestPractice, brought went 413 to 812 and individual 1,103 to 704. The
   total did not change. A session predicted the brought budget would need
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

**Meanwhile the whole is not capped.** The practice's own rule says "a cap
on one part is not a cap on the whole." In this session the session-start
hook put about 3,900 tokens into context; the session file it carries
measures about 2,300. The other 1,500 or so (the list of spoken commands and
the source-resolution notes) is in no budget.

**The next two blocks are already visible.** The ladder set's occasion share
is at 695 of 750 (93%) and its AGENTS.md at 1,352 of 1,400 (97%). The next
rule added to that set refuses.

## Options considered

### A. Keep the pots, and make every move between them automatic

Write an offset for each route: when a rule moves between sets, move its
tokens between the budgets that pay for it; when a set is copied in, move
its share from brought to the repository (done today for that one route).

**Holes.** The routes are open-ended, so this is the same route-by-route
patching that has not held. The pots live in different repositories (the
ladder share in the ladder set, the brought budget in the individual set,
the ceiling in each consumer), so one move has to write approvals in three
repositories together, which no tool does atomically. And it leaves every
pot as tight as before, so ordinary growth still asks. **Rejected.**

### B. Raise every pot with real headroom

Raise each budget to, say, 50% over what it measures.

**Holes.** Quick, and it stops the asks for a while. But tokens moving
between pots still overflow the smaller ones, and the asks come back as
soon as any one pot fills. It is the band-aid. **Rejected.**

### C. Remove the budgets

**Holes.** Before 2026-09-11 AGENTS.md grew every day with nobody deciding
it (the occasion index alone grew about 160 tokens a day). That problem
comes straight back. **Rejected.**

### D. One total per session, and the parts become notices (proposed)

**Only one number refuses: the total a session in a given repository loads**
-- every always-loaded file, plus what the session-start hook adds, from
every source. Every part's number (resident cap, occasion share, brought,
individual, each surface's ceiling) stays as a **notice** that says which
part grew, and never refuses.

**The total is declared once, by the person, in their individual set**
(`session_load_tokens`), so it travels to every repository they work in,
the way `brought_sets_tokens` does now. One number, one approval. A
repository may declare its own total only when it needs to differ.

**Attacking it:**

- *Moves, copy-ins and accounting fixes.* They do not change the total, so
  they never ask. This is the point.
- *"The total must fit BestPractice, so consumers get a loose limit."*
  True: BestPractice's own AGENTS.md is the largest. But the cost that
  matters is what one session pays, and if a session in BestPractice may pay
  N, a session in a consumer paying N is the same cost. A repository that
  wants tighter declares its own.
- *"It loses the forcing decision the tight occasion cap was for"* (Morgan,
  2026-09-14, option D: "the cap is meant to be met soon and often"). Yes,
  and that is the trade being asked for: a decision per index line was the
  frustration. The notices keep the information -- which part grew, by how
  much -- and a headroom notice at 90% of the total says when a reduction
  pass is due, before anything refuses.
- *Real growth still asks.* Yes, when the total crosses, after a reduction
  pass, exactly as the practice says today. That should be rare: real
  growth is slow next to the structural moves above.
- *Other people's installs* (Alex's, or anyone's who does not declare a
  total). Nothing changes for them: the per-part refusals stay in force
  wherever no total is declared. It is opt-in.
- *The uncounted hook output.* Counting it makes the total honest, and it
  goes in the same measurement.

## The proposal

1. **Engine (BestPractice).** `build_views.effective_budgets()` and the
   session check compute one `session_load_total` per repository: AGENTS.md,
   CLAUDE.md, and the session-start hook's full output. Where the person (or
   the repository) declares `session_load_tokens`, that total is the one
   check that refuses (`session-load-budget`), and `loader-within-caps`,
   `session-file-allowances-fit`, the brought and individual rows of the
   session check, and [build_views.py](../tools/build_views.py)'s occasion-share refusal report
   instead of refuse. `budget-within-approval` covers the total and stops
   requiring an approval for each part. With no total declared, everything
   behaves as today. Tests in [tools/verify_harness.py](../tools/verify_harness.py) for both paths, plus
   one that moves a rule between two sets and asserts nothing refuses.
2. **Practice text.** [session-load-budget](../practices/session-load-budget.md)
   and [reduction-pass](../practices/reduction-pass.md) say the total is what
   refuses where one is declared, and the parts are where to look when it
   grows.
3. **Morgan's number** goes in the individual set as `session_load_tokens`,
   with his words in its approvals. Suggested: the largest total measured
   across his repositories plus 20%, given to him measured before he picks.
4. **Rollout** by Update Vendors to every consuming repository; each one's
   per-part approvals stay in place as notices until a later cleanup.

**Effort:** about three to four hours of session work for steps 1 and 2,
then an Update Vendors run.
