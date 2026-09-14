<!-- Last updated: 2026-08-31 (Buenos Aires) by the review-arm experiment session -->

# Pre-registered prediction for the review arm

**Written before any review-arm prompt was answered.** It is committed in
this state; the result in [spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md)
is reported against it whatever it says. This is the fourth run of one eval
(v1 → v2 → v3/v4/v5 → this), which is exactly the situation
[evals/routing/PREDICTION.md](PREDICTION.md) wrote itself against for the
same reason: a measurement re-run until it moves means nothing, and the
protection is saying in advance what is expected and not revising it after
seeing the answers.

## What is being added

One arm, `review`, in [tools/routing_eval.py](../../tools/routing_eval.py).
Per spec/ATTENTION_CEILING.md's design: the treatment arm's context
(resident block, occasion index, and the path channel's output for the
files the change touches) plus the completed diff, asked the oracle's
question — *"which of these genuinely applied?"* — rather than the
control's prospective one. No task description, no framing of work still to
do.

**One hop, not two — the cheapest version, as the source document
explicitly permits ("the same two hops as the treatment if you want the
comparison clean, or one hop if you want the cheapest version; run
whichever, but say which").** The choice: one hop. Reasons —

1. The recommendation this experiment tests is a prefilter feeding a judge
   pass, not a second round of a session's own judgment about what to open.
   The loader has already decided what it surfaces; replaying treatment's
   request/open cycle would be testing a mechanism (self-selection of which
   Rules to read) that the recommended architecture does not itself use.
2. It is the cheaper run, and the source document's own reading table
   grades the outcome on recall and on the oracle-free head-to-head, neither
   of which depends on hop count.
3. The nothing-hidden risk is smaller for one hop, not larger: the review
   arm sees every Rule the loader would ever show for this case in a single
   prompt, with no opportunity to have "asked for less than everything
   available" the way treatment's hop 1 can.

Measured cost bears this out post-implementation: review arm ≈4,636
tok/case against treatment's ≈4,619 (the loader's context, essentially
unchanged by dropping the task description and the second-hop machinery).

## The prediction

Reusing spec/ATTENTION_CEILING.md's own reading table, because it was
written for exactly this result and re-deriving a different one now would
be the tuning-after-seeing-the-number failure this document exists to
prevent:

- **≈84% or better** → framing is what matters, and it is available at the
  loader's price. Build the architecture spec/ATTENTION_CEILING.md
  recommends (review pass as primary control, closed per-practice
  questions, loader as prefilter).
- **≈77%** → the loader's context is the limit, not the framing. The
  architecture change buys nothing measured here; the answer is enforcement
  and a smaller catalogue.
- **≈90%+** → the strongest case, and the strongest argument for making
  review the primary control immediately.

**Point prediction: 80–86%, most likely close to control's 84%.** Framing
is the larger measured effect in this whole eval (16 points, versus
loading's 7), and the review arm gets the oracle's own framing. The
loader's context is 48% smaller than control's, which is the one thing
that could pull it down from control's 84% — but the miss set that
routing changes have moved (v3 → v5) has consistently been small in this
eval's own stated resolution (≈15 points on 20 cases), and cutting the
practice text roughly in half is a much smaller manipulation than the
prospective/retrospective framing difference that produced 16 points on
identical, complete input. If the review arm mostly recovers the framing
gain, the cost of missing content should show up as a few points of
recall, not most of the gap.

## Failure / unconvincing criteria — read before the number, not after

- **A result under about 10 points above control's 84% (i.e. under ≈94%,
  practically meaning anything not clearly separated from control) is
  read as unconvincing, not a win.** This is spec/ATTENTION_CEILING.md's
  own stated mitigation for the framing confound: the review arm shares
  the oracle's framing and the oracle defines truth, so some of any
  agreement is by construction. A small win could be that construction,
  not merit.
- **The primary de-confounded signal is the oracle-free head-to-head**
  (review vs. control, raw answer sets, oracle not consulted for the
  comparison at all) — implemented in `cmd_score` as `rc_h2h`. If review
  finds materially more than control loses relative to it (not merely
  "review's truth-scored recall is higher"), that is evidence the effect
  is real rather than an artifact of shared framing.
- **≈77% or below** falsifies the recommendation outright per
  spec/ATTENTION_CEILING.md: the loader's context, not the framing, is the
  binding constraint, and the review-pass architecture buys nothing this
  eval can measure. In that case the correct next move is *not* another
  routing pass — three of those (v3, v4, v5) have already returned the
  same null result — but enforcement and catalogue reduction, per
  spec/ATTENTION_CEILING.md's "supporting moves" section.
- **Precision or cost drifting far from treatment's** would say the review
  framing changed what gets surfaced, not just how it is judged — it
  should not, since the context-building code is shared with the
  treatment arm's hop 1 verbatim (`loader_block()` + `path_channel()`);
  a large drift would point at an implementation bug in the new arm
  rather than at a finding, and should be treated as one first.

## What this run does not attempt

The second experiment spec/ATTENTION_CEILING.md names — closed
per-practice yes/no questions instead of one open question over the
candidate set — is conditional ("if the first validates") and is not run
here. Whether to run it depends on this result and is a decision for
after scoring, not before.

## Method, restated from the source document

- One isolated session per cell (20 cases), reading only its own prompt
  file. The arms contaminate each other otherwise — this run assigns each
  case to a freshly-started subagent with no memory of any other case or
  arm.
- The oracle and control prompts are untouched by this change — verified
  byte-identical to v3's baseline (`ef4e9cc`) across all 40 oracle+control
  prompts, regenerated in a worktree and diffed, both before this file was
  written and to be re-verified after the review arm lands.
- The current answer set is preserved at
  `evals/routing/answers-v5-pre-review-arm/` before anything in
  `evals/routing/answers/` is added to.
- The occasion index is not tuned to move this number. Nothing in
  `practices/*.md` or `tools/routing_scope.json` changes as part of this
  experiment.
