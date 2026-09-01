<!-- Last updated: 2026-09-01 (Buenos Aires) by the attention-ceiling follow-up session -->

# Pre-registered prediction for the gloss-tier experiment

**Written before any gloss-tier prompt is authored or answered.** This is
candidate design 1 from
[spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md)'s "Candidate
designs for a future attempt" section, promoted to its own pre-registered
run per that section's own condition: "any of what follows still needs its
own `PREDICTION`-style file with numeric targets and failure criteria,
committed before it runs." Nothing below has been run yet — this file exists
so that running it, when it happens, follows the same discipline as v1
through the review arm rather than being tuned after seeing a number.

## What is being added

A **gloss tier** per practice: a short (target ≈40–60 token) paragraph, one
level between the occasion index's 80-char `index_clause` and the full
`## Rule`+`## Detail` text — structurally OpenViking's L1, as named in
ATTENTION_CEILING.md's external-precedent section. Authored once per
practice **from the practice's own Rule text**, mechanically or by a fixed
prompt applied uniformly to all 52 — never hand-fitted to the 20 eval cases,
per the same document's standing prohibition on tuning after seeing a
result.

A new arm, `review-gloss`, in
[tools/routing_eval.py](../../tools/routing_eval.py): the review arm's exact
context and framing (loader's resident block + occasion index + path-channel
output, judge-only, retrospective, one hop) plus one addition — every
candidate the occasion index surfaces by one-line clause also carries its
gloss paragraph, inline, in the same prompt. No second hop, no
request/open cycle. This isolates the gloss tier from the other candidate
fix (idea 2, more judge-pass budget via a second hop) on purpose: the
diagnosis in ATTENTION_CEILING.md's review-arm section named both as viable
and said running them separately would say which closed the gap.

## The prediction

Anchored to the two numbers already measured for the same 20 cases, same
loader, same judge-only framing:

- **Review arm (clause only): 54%.**
- **Treatment arm (two-hop, full Rule on request): 77%.**

The gloss tier's own claim is that a clause was the review arm's actual
failure mode (c07's three-practice miss, diagnosed in ATTENTION_CEILING.md,
was clause-only exposure, not judgment on content seen). If that diagnosis
is right, a gloss paragraph should recover most, not all, of the 23-point
gap to treatment — a gloss is denser than a clause but still lossy against
the full Rule a two-hop request would fetch.

- **≥70%** → the gloss tier closes most of the clause-vs-full-Rule gap at
  one hop's cost. Worth building as a format change across all 52
  practices, ahead of idea 2 (more judge-pass budget) since it is cheaper
  per case (no second round-trip).
- **58–69%** → real but partial recovery. Worth stating explicitly which
  practices still miss and whether they cluster (e.g., practices whose Rule
  does not compress to 60 tokens without losing the distinguishing detail) —
  that failure shape decides whether gloss tier plus idea 2's second hop is
  the right combination, or whether idea 2 alone would have gotten here
  anyway.
- **≤57%** → the gloss tier does not move the needle beyond noise of the
  54% baseline. The diagnosis that "a clause was all it ever saw" was
  necessary but not sufficient — reading *more* text is not, on its own,
  what treatment's second hop was doing; something else about the two-hop
  design (the act of requesting by name, not just what comes back) is
  carrying the weight. In this case, per ATTENTION_CEILING.md's standing
  guidance, this result is not grounds to retune the gloss length and
  re-run — it is grounds to test idea 2 as its own experiment before
  concluding tiering doesn't work here at all.

**Failure criteria stated before running, not after:** a result inside 5
points of 54% (49–59%) counts as "the gloss tier did not help," full stop —
not as a partial win requiring a second look at gloss wording. This mirrors
ATTENTION_CEILING.md's own "under about 10 points above control is
unconvincing" guard against reading noise as signal.

## Confounds to state now, not discover later

- **Authoring the gloss uniformly is itself a judgment call.** A gloss
  written by an LLM from the Rule text is not free of the same
  framing-sensitivity this whole document is about. Fixed prompt, applied
  to all 52 in one pass, committed before the eval runs, is the discipline
  that keeps this honest — the same guard PREDICTION_REVIEW_ARM.md applied
  to the review prompt itself.
- **This does not use the answer key for candidate selection**, same as the
  review arm's oracle-free head-to-head: report review-gloss vs. review
  (clause-only) practices found/missed directly, not only via oracle
  agreement.
- **Token cost must be reported alongside recall.** A gloss tier that closes
  the gap by roughly doubling context back toward treatment's ≈4,619 tokens
  has not demonstrated a cheaper path to treatment's number — it has
  demonstrated treatment, authored differently. The interesting result is
  recall gained per token spent over the 54% baseline, not recall alone.

## Rules for running it

Same as every prior run in this line: pre-register (this file), do not
touch the oracle/control/treatment/review prompts, one isolated session per
cell, preserve `answers-*` directories per arm rather than overwriting them.

## What this file is not

Authorization to build the gloss tier as a permanent format change. Per
ATTENTION_CEILING.md's own header on the candidate-designs section: "this is
not authorization to run another routing pass." This is the pre-registration
that makes running it, if someone decides to, accountable to a number stated
in advance — the decision to spend the session on it is separate and has not
been made here.
