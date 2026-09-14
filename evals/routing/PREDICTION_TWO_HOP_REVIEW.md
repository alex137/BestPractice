<!-- Last updated: 2026-09-01 (Buenos Aires) by the attention-ceiling follow-up session -->

# Pre-registered prediction for the two-hop review arm

**Written before any two-hop-review prompt is authored or answered.** This
is candidate design 2 from
[spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md)'s "Candidate
designs for a future attempt" section, promoted to its own pre-registered
run for the same reason [PREDICTION_GLOSS_TIER.md](PREDICTION_GLOSS_TIER.md)
was: nothing in that section runs without its own numeric targets and
failure criteria, committed first.

## Why this one, now

[The gloss-tier result](../../spec/ATTENTION_CEILING.md#the-gloss-tier-result-2026-09-01)
falsified candidate 1 at 53.7% — flat against the review arm's 54%, despite
nearly doubling token cost. The result that matters more than the flat
recall number: the **oracle-free head-to-head against the review arm was
27-vs-36, not a superset**. Review-gloss did not simply find more of what
review found; it found a substantially different, equally incomplete set.
That is not the signature of "not enough text per candidate" (which should
mostly add hits without dropping others) — it is more consistent with
**the fixed, uniform gloss helping some cases and hurting others by
crowding the same context budget**, which points at a mechanism gloss
cannot supply: **letting the judge choose, per case, which few candidates
are worth full text**, rather than a fixed-size summary applied to all of
them alike. That is what treatment's second hop does and review's one-hop
design does not.

## What is being added

A `review-hop1` / `review-hop2` pair in
[tools/routing_eval.py](../../tools/routing_eval.py), structurally the
treatment arm's two hops but with the review arm's judge-only, retrospective
framing at both:

- **Hop 1**: the review arm's exact context (resident block, occasion
  index's one-line clauses, path-channel output, the completed diff) minus
  a final answer — instead, name the practices whose full Rule you want to
  see before judging. Judge-only framing throughout: no task description,
  the diff is already finished.
- **Hop 2**: exactly the Rules requested (resolved by the harness, same
  `build_hop2_prompt` machinery treatment already uses) plus the
  path-channel output, judge-only framing, final answer.

This isolates the "choice" mechanism from the "more text" mechanism the
gloss tier tested: hop 2 sees full Rules, same as treatment's hop 2, but
only for what the judge itself chose to open, not a fixed gloss applied
uniformly to every candidate.

## The prediction

Anchored to the three numbers already on record for these 20 cases:

- **Review (one hop, clause only): 54%.**
- **Review-gloss (one hop, clause + uniform gloss): 53.7%.**
- **Treatment (two hop, doing-the-work framing): 77%.**

If the diagnosis above is right — the second hop's *choice* mechanism is
what treatment's advantage actually rests on, not its framing or its raw
token count — then review-hop2 should land close to treatment's 77%,
since the only remaining difference between them is prospective-vs-
retrospective framing, which [the review-arm result](../../spec/ATTENTION_CEILING.md#the-review-arm-result-2026-08-31)
already showed costs points in the *other* direction (retrospective framing
underperformed prospective framing once, at 54% vs 84%/77%).

- **≥70%** → the second hop, not the framing, was carrying treatment's
  result. This is the strongest case yet for building the architecture
  ATTENTION_CEILING.md's original recommendation described (loader as
  prefilter, judge pass with a real second hop) — worth doing despite the
  now twice-falsified simpler versions of "review as primary control."
- **58–69%** → partial recovery. The second hop matters but framing still
  costs real points on top of it — worth stating which cases still miss
  and whether they're clause-only misses (never requested) or
  requested-but-still-missed (judged and declined) misses, since that
  distinguishes a residual reach problem from a residual judgment problem.
- **≤57%** → inside noise of both prior retrospective-framing results
  (54%, 53.7%). If a real second hop *also* doesn't move the number, the
  conclusion is not about text budget or choice mechanism at all — it is
  that judge-only, retrospective framing itself has a ceiling somewhere
  around 54%, independent of what context it is given, and every
  remaining candidate design in this document that keeps that framing
  (all three) is worth abandoning rather than incrementally re-tried.

**Failure criterion stated before running:** a result inside 5 points of
54% (49–59%) counts as "the second hop did not help either," full stop —
same guard as the gloss-tier prediction, for the same reason.

## Confounds to state now

- **This is the third arm sharing the oracle's judge-only framing**, after
  review and review-gloss. Any of the three could be scoring well partly by
  construction (framing-similarity to the answer key), which is why the
  oracle-free head-to-head against review (raw sets, not truth-filtered)
  matters as much as the recall number here, same as it did for the gloss
  tier.
- **Token cost must be reported.** Hop 1 costs about what review already
  costs (≈4,781 tok); hop 2's cost depends on how much each case requests,
  and needs to be measured, not assumed — a judge that over-requests out of
  caution would land near control's ≈8,964 tok for a two-request-round
  answer, which is a materially different cost story than treatment's
  ≈4,619 (hop 1) + hop-2 cost.
- **This does not retry the gloss tier with a bigger gloss.** It tests a
  structurally different mechanism (choice vs. fixed summary), per this
  document's standing rule against tuning a falsified experiment's
  parameters and re-running it.

## Rules for running it

Same as every prior run in this line: pre-register (this file), do not
touch the oracle/control/treatment/review/review-gloss prompts or answers,
one isolated session per cell per hop, preserve existing `answers-*`
directories.

## What this file is not

Authorization to build a permanent review-pass architecture. The decision
to spend further session time productizing this, if the number supports
it, is separate from pre-registering the number that would justify it.
