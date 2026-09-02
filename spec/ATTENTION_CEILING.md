<!-- Last updated: 2026-09-01 (Buenos Aires) by the follow-up session that ran the gloss-tier and two-hop-review experiments -->

# The Attention Ceiling — What Six Runs Measured, and What To Do About It

Written for the session that takes this on next. It carries a finding, the
recommendation that finding argued for, three experiments that tested the
recommendation and its two most direct follow-ups, and the result: **all
three falsified it.** Read it in full; it is short and it changes what the
next phase is for.

**The one-sentence version:** the routing eval's miss rate is mostly not a
loading problem, the loader is already within noise of the best any routing
architecture can do, the largest measured effect in the whole eval (framing)
looked like an opportunity — and three cheap tests, in order, closed it:
the review arm scored **54%** (below the loader's own working-session recall
of 77%), a gloss tier on top of it scored **53.7%**, and a real second hop
on top of that scored **50.5%** — the lowest of the three, at
control-level token cost. Judge-only, retrospective framing has a ceiling
around 54% on this eval regardless of how much context or choice it is
given. See [The review-arm result](#the-review-arm-result-2026-08-31),
[the gloss-tier result](#the-gloss-tier-result-2026-09-01), and
[the two-hop review result](#the-two-hop-review-result-2026-09-01) below.

## The finding

| arm | practice context | misses of 95 applicable |
|---|---|---|
| **Oracle** — all 52 Rules, asked only to classify | ≈8,901 tok | — *(the answer key)* |
| **Control** — all 52 Rules, asked to do the work | ≈8,898 tok | **15 (16%)** |
| **Treatment** — the loader | ≈4,642 tok | **22 (23%)** |

**The oracle and the control receive the same 52 Rules and the same diff.**
Both are shown the completed change. They differ in exactly two ways: the
control is told it has a task to perform, and it is asked *prospectively* —
"which of the practices above are you going to apply to this work?" — where
the oracle is asked *retrospectively*, "which genuinely applied?"

That difference costs **16 points**. Loading costs a further **7**.

So the ceiling on this task is 84%, and it is set before the loader is
involved at all. Three phases of work have gone into the smaller half of the
problem.

### This is not an inference from one run

| run | what it asked | answer |
|---|---|---|
| v3 | does residency produce compliance? | No. `verify-postcondition` was resident and named 0 of 3 times. |
| v4 | does fixing a wrong glob help? | The practice was surfaced on every case it applied to, and **every remaining miss was a case where the session had been shown it and declined**. |
| v5 | does a catalogue-wide routing pass help? | Misses 21 → 22 at 8% more context. The practices a session was *never shown* fell 13 → 11; the practices it *was* shown and missed rose 8 → 11. |

Three different manipulations of the routing layer, three times no movement in
the total. The v5 result is the cleanest: **routing changes convert reach
failures into judgment failures without changing how many failures there
are.**

### Why this is not fatal

It is worth saying plainly, because "23% missed" sounds like it kills the
system and it does not:

- **The 7-point loading penalty is inside this eval's stated resolution.** The
  loader delivers 77% recall for 48% less context than carrying everything. On
  recall per token it is nearly twice as efficient as the control, and always
  has been.
- **A practice with a working check has no miss rate.** Enforcement bypasses
  the routing question entirely, and 15 of the 22 remaining misses are on
  practices that now carry one ([spec/ENFORCEMENT.md](ENFORCEMENT.md)).
- **The eval measures naming, not following.** It says so in its own output.
  A session that never names `doc-references-are-links` but writes correct
  links has not failed; the eval scores it as a miss.

What the finding does kill is the belief that more routing will fix this.

## The recommendation

**Tested below and falsified — kept here as the argument that was tested,
not as current guidance.** See
[The review-arm result](#the-review-arm-result-2026-08-31) for the verdict
and the [supporting moves](#the-supporting-moves-whatever-the-experiment-says)
for what to do instead.

**Move the decision point from before the work to after it.**

Every channel built so far — resident, path-triggered, occasion index,
gate — is *ex ante*: get the right practices in front of the session before it
starts. That is exactly where attention is worst, because the catalogue
competes with the task. The one manipulation in this eval that moves behaviour
16 points is asking about a finished change instead of a planned one.

Three parts:

**1. A review pass over the diff becomes the primary control.** After the work
is drafted and before it lands, one pass whose only job is to judge the change
against practices. **This is not the plan's periodic deep check** — that is a
big, open-ended, whole-catalogue review, which the plan itself identifies as
the mechanism that already failed. This is per-change and narrow.

**2. Closed questions, one practice at a time.** *"Which of these might apply
to what I am about to do?"* is open-ended and dilutes. *"Does this diff violate
this rule — yes or no, with the offending line?"* is closed. Closed is where
the oracle's advantage plausibly comes from, and it fans out across candidate
practices rather than asking one question about all of them.

**3. The loader becomes the prefilter for that pass, not context for the
working session.** This is the part that repurposes three phases of work
rather than discarding it. A prefilter does not need high recall or good
precision — it needs to be cheap and over-inclusive, which is what 77% recall
at 4,642 tokens is. And the working session stops carrying practice text at
all, which is a far larger context saving than the loader was built to
deliver.

The architecture, stated once: **the loader picks candidates, a separate pass
judges them one at a time against the finished work, and checks handle
whatever can be mechanised.** Practices stop being something a session reads
and become something a change is tested against.

## Run this experiment first

The recommendation above is an argument. It should be measured before it is
built, and it can be, cheaply, with the machinery that already exists.

### The review arm

Add one arm to [tools/routing_eval.py](../tools/routing_eval.py):

| arm | context | framing | result |
|---|---|---|---|
| oracle | all 52 Rules | judge only | *(answer key)* |
| control | all 52 Rules | doing the work | 84% |
| treatment | the loader | doing the work | 77% |
| **review** | **the loader** | **judge only** | **?** |

The `review` prompt is the treatment's context — resident block, occasion
index, and the path channel's output — with the completed diff, asked the
oracle's question rather than the control's. No task to perform. It is the
same two hops as the treatment if you want the comparison clean, or one hop if
you want the cheapest version; run whichever, but say which.

**How to read the result:**

- **≈84% or better** → framing is what matters, and it is available at the
  loader's price. Build the architecture.
- **≈77%** → the loader's context is the limit, not the framing. The
  architecture change buys nothing and the answer is enforcement and a smaller
  catalogue.
- **≈90%+** → the best case, and the strongest possible argument for making
  review the primary control.

**One confound to state in the write-up, not to discover later.** The review
arm shares the oracle's framing, and the oracle *defines* truth here — so some
agreement is by construction, not by merit. Two mitigations: report the
oracle-free head-to-head (practices `review` found that `control` missed, and
vice versa), which does not use the answer key for the comparison at all; and
treat a result under about 10 points above the control as unconvincing rather
than as a win.

### A second experiment, if the first validates

Does a **closed per-practice question** beat one open question over the
candidate set? Same cases, same prefilter, but ask *n* separate yes/no
questions instead of one "which of these apply". More expensive per change and
the thing the architecture actually proposes, so it is worth knowing whether
the closed framing is where the gain is or whether retrospection alone
accounts for it.

### Rules for running it

- **Pre-register.** Write the prediction and the failure criteria to a file
  and commit it *before* running, as
  [evals/routing/PREDICTION.md](../evals/routing/PREDICTION.md) did. This is
  the fourth run of one eval; a measurement re-run until it moves means
  nothing.
- **Do not touch the other arms.** The oracle and control prompts have been
  byte-identical across v3, v4 and v5, verified by regenerating them in a
  worktree and diffing. Keep it that way and their 40 answers stay reusable.
- **One isolated session per cell**, reading only its own prompt file. The
  arms contaminate each other otherwise.
- **Preserve the current answer set** beside the new one, as
  `answers-v5-pre-review-arm/`.

## The review-arm result (2026-08-31)

Run against [evals/routing/PREDICTION_REVIEW_ARM.md](../evals/routing/PREDICTION_REVIEW_ARM.md),
written and committed before any review-arm prompt was answered. **The
prediction was 80–86%. The result was 54%** — below the ≈77% floor the
prediction itself named as the falsifying outcome, and outside the predicted
range in the direction the prediction did not budget for at all.

| arm | practice context | framing | recall | miss |
|---|---|---|---|---|
| Control | ≈8,905 tok | doing the work, prospective | 84% | 16% |
| Treatment | ≈4,619 tok | doing the work, prospective (two hops) | 77% | 23% |
| **Review** | **≈4,636 tok** | **judge only, retrospective (one hop)** | **54%** | **46%** |

Oracle-free head to head (raw answer sets, control vs. review, oracle not
consulted for the comparison — the confound mitigation the source prediction
named): control named **59** practices review did not; review named **18**
control did not. Review recall minus control recall is **−31 points** — not
"under 10 points and unconvincing," but negative and large. There is no
ambiguity to read here.

**Verdict per the pre-registered reading table: falsified, decisively.**
"≈77% or below" was the document's own stated threshold for "the loader's
context is the limit, not the framing; the architecture change buys nothing
and the answer is enforcement and a smaller catalogue." 54% clears that bar
with room to spare. **The recommended architecture is not built.**

### Why it landed below the loader's own working-session recall, not just below control

This needed root-causing rather than accepting as a bare number, because it
is a genuinely surprising result: the review arm was given the *same* loader
context as the treatment arm's first hop (resident block, occasion index,
path-channel output — ≈4,636 tok against treatment's ≈4,619), yet scored 23
points below treatment's 77%, not just below control's 84%. Same nominal
context, worse result than the arm that also only carries the loader.

The mechanism is visible case by case. Take c07 (5 applicable practices):
treatment's first hop, reading only the occasion index's one-line clauses
for anything not resident or path-surfaced, *requested* eight candidates by
name, including three — `layered-practice-packs`, `registry-source-of-truth`,
`readers-vocabulary` — that are not resident and were not surfaced by the
path channel. The harness then resolved those requests and handed back their
full Rules, and the second hop kept most of them: 6 of 8 named, 5 of 5
applicable found. The review arm, given the identical resident block, the
identical path-channel output, and the identical occasion-index one-liners
for the same case, named only `practice-export-loop` and
`doc-references-are-links` — the two that happened to be path-surfaced in
full. It never had a turn to ask "tell me more about
`layered-practice-packs`," because the one-hop design this run chose has no
such turn. It missed `layered-practice-packs`, `registry-source-of-truth`
and `readers-vocabulary` outright — not because it judged them and declined,
but because a one-line occasion-index clause was all it ever saw of them, and
a clause is not enough to affirm that a practice applies.

**This is a real cost of the one-hop design choice, stated in the
pre-registration as the "cheapest version" and reasoned there to be a small
risk. The reasoning was wrong, and the result is why:** the treatment arm's
second hop is not a formality. Reading the full Rule of a candidate before
judging it is doing real work — arguably more of the work than the framing
question this experiment set out to isolate. A one-shot judge pass over a
prefilter's raw output is not the same instrument as "the loader, used
properly," and this run measured the former while the recommendation's own
language ("the loader picks candidates, a separate pass judges them") more
plausibly describes the latter.

**This does not rescue the recommendation, and is not grounds to re-run the
experiment with a two-hop version to see if the number improves.** Doing
that now, after seeing this result, is exactly the tuning-after-the-fact
pattern this whole eval's discipline exists to prevent — the same reasoning
that stopped this session from narrowing globs after seeing a cost number a
phase ago. The verdict stands on the pre-registered criteria: **54% falsifies
the recommendation as tested.** What the case-level analysis adds is not a
reason to discount the result — it is a sharper diagnosis of *why* a
judge-only pass over a prefilter's raw output underperforms even the
existing loader, which matters for anyone who revisits this question later
with a cleanly two-hop design and a fresh pre-registration of their own. That
is future work, named and left there, not retried here.

### What was not run

The second experiment (closed per-practice questions instead of one open
question) was explicitly conditional on this one validating — it did not,
so per [evals/routing/PREDICTION_REVIEW_ARM.md](../evals/routing/PREDICTION_REVIEW_ARM.md)'s
own terms it is not run.

## The gloss-tier result (2026-09-01)

Candidate design 1 (below), pre-registered as
[evals/routing/PREDICTION_GLOSS_TIER.md](../evals/routing/PREDICTION_GLOSS_TIER.md)
and then actually run against the same 20 cases, same oracle, same one-hop
judge-only framing as the review arm — the only change is that every
non-resident practice's occasion-index clause is now paired with a
mechanically-extracted ≈55-word gloss (first 55 words of `## Detail`,
truncated, never hand-fitted per practice or per case).

| arm | practice context | framing | recall | miss |
|---|---|---|---|---|
| Review (clause only) | ≈4,781 tok | judge only, one hop | 54% | 46% |
| **Review-gloss** | **≈8,177 tok** | **judge only, one hop** | **53.7%** | **46.3%** |

**53.7% is inside the pre-registered 49–59% band the prediction named as "did
not help, full stop."** It is not a rounding-distance win; it did not move at
all, while very nearly doubling the review arm's own token cost — ≈8,177
tokens against control's ≈8,964, essentially as expensive as carrying the
whole catalogue, for the same recall as the cheap 54% baseline.

**The oracle-free head-to-head is the sharper result, and it is not "same
answer, more expensively."** Comparing raw answer sets between review-gloss
and review, without touching the oracle: review-gloss named 27 practices
review did not, and missed 36 that review had found. That is large churn in
both directions on a flat total — the gloss tier did not fail to move the
needle by leaving the same practices found; it found a substantially
different, equally-incomplete set. Whatever the gloss paragraph is adding for
some candidates, it is costing something on others, and the net across 20
cases is a wash.

**This directly narrows the diagnosis the review-arm write-up left open.**
That diagnosis said a one-line clause was what c07 (and cases like it) never
got more than, and reasoned that more text per candidate should recover some
of the gap to treatment's two-hop 77%. It did not. The plausible reading,
stated but not further tested here per this document's own rule against
re-running a falsified experiment with a tuned variant: **candidate design
2 — a second hop, i.e. actually being able to ask for a named practice's full
Rule — was doing more of treatment's work than "more text up front" is.** A
gloss is still a summary chosen in advance for every case; a second hop lets
the judge choose, per case, which four or five candidates are worth the full
text. That is a different mechanism, not a bigger version of this one, and
per this document's standing discipline it needs its own pre-registration
before anyone spends a session on it — not a retry of this file with a
longer gloss.

**Verdict per the pre-registered reading table: falsified.** The gloss tier,
as specified, is not the fix. Candidate design 3 (tagging) was already
predicted, before this run, to inherit the same null result on this
document's own routing-pass precedent, and nothing here changes that
reasoning.

## The two-hop review result (2026-09-01)

Candidate design 2, pre-registered as
[evals/routing/PREDICTION_TWO_HOP_REVIEW.md](../evals/routing/PREDICTION_TWO_HOP_REVIEW.md)
and run the same day as the gloss tier, directly off that result's own
diagnosis: gloss-tier's 27-vs-36 oracle-free churn against the review arm
suggested a fixed, uniform summary was not the mechanism treatment's 77%
depends on, and that letting the judge choose which candidates to open in
full — a real second hop, judge-only framing throughout, structurally
identical to treatment's two hops except retrospective rather than
prospective — might be.

| arm | practice context | framing | recall | miss |
|---|---|---|---|---|
| Review (one hop, clause only) | ≈4,781 tok | judge only, retrospective | 54% | 46% |
| Review-gloss (one hop, clause+gloss) | ≈8,177 tok | judge only, retrospective | 53.7% | 46.3% |
| **Review-hop2 (two hop, full Rule on request)** | **≈8,350 tok** (hop1 ≈4,788 + hop2 ≈3,562) | **judge only, retrospective** | **50.5%** | **49.5%** |

**50.5% is not just inside the pre-registered ≤57% band — it is the lowest
of the three retrospective-framing arms**, at a token cost matching
control's ≈8,964 for a two-round exchange. The judge got exactly what
treatment's hop 2 gets — the full Rule of every practice it asked to see —
and scored below the one-hop clause-only arm that saw far less text.

**This closes the question the gloss-tier write-up left open, in the
direction the ≤57% branch of that prediction named.** It was not "not
enough text" (gloss tier) and it was not "the judge couldn't choose what to
read" (this run) — both were given the mechanism they were missing and
neither moved the needle. All three retrospective-framing arms now cluster
at 50–54%, while the two prospective-framing arms (control 84%, treatment
77%) sit 23–34 points higher on the same 20 cases, same oracle, same
practice catalogue. **The variable that predicts the score across five runs
of this eval is not context, not token budget, not whether the judge can
request full text — it is whether the session is asked "what will you do"
or "what did someone else do."** Every remaining idea in this document that
keeps retrospective, judge-only framing (tagging, more resident budget
spent on the judge pass) inherits the same ceiling on this evidence, not
just on precedent from the routing-pass history.

**Verdict per the pre-registered reading table: falsified**, and by the
document's own stated criterion for the ≤57% branch — every remaining
candidate in this document that keeps judge-only, retrospective framing is
not worth separately re-testing; the framing itself is the ceiling, not
what accompanies it.

## The catalogue re-run (2026-09-02)

**Why this ran.** `tools/routing_eval.py`'s recall/miss figures, and the
answer files under `evals/routing/answers/`, were frozen against a
52-practice snapshot (`ef4e9cc`, 2026-08-31). The catalogue grew to 54
(`checkable-gets-checked`, `todo-is-a-handoff`) and neither new practice
had ever been scored — a 2026-09-02 independent deep-check audit found the
gap, plus a smaller bug: the script hardcoded the literal string `"52"` in
several prompt/output labels even though it dynamically assembled all 54
practices' Rules into the prompt (`build_prompt`'s oracle/control framing
text, and `cmd_score`'s table header and arm labels). Both are fixed —
labels now read `len(practices)`/`len(valid)` — and all five answer sets
(oracle, control, treatment1, treatment2, review; 100 files) were
regenerated from scratch: fresh independent judgments against the full
54-practice catalogue and current `AGENTS.md` loader block, not a patch
onto the old 52-practice answers.

**The fresh numbers, this run:**

| arm | recall | miss | precision |
|---|---|---|---|
| Control (all 54 loaded) | 64% | 36% | 77% |
| Treatment (resident + index, two hop) | 62% | 38% | 62% |
| Review (loader, judge-only) | 78% | 22% | 51% |

**The number that actually matters here is not any single row above — it is
how far all three rows moved from the last recorded run**, reproduced
exactly by re-scoring the old (pre-fix) answer files unchanged before they
were overwritten:

| arm | 2026-08-31 (52-practice, frozen) | 2026-09-02 (54-practice, fresh) | swing |
|---|---|---|---|
| Control | 84% recall / 16% miss | 64% recall / 36% miss | **20 points** |
| Treatment | 77% recall / 23% miss | 62% recall / 38% miss | **15 points** |
| Review | 54% recall / 46% miss | 78% recall / 22% miss | **24 points** |

Two new practices out of 54 (3.7% of the catalogue) cannot honestly account
for a 15-24 point swing in any arm, let alone one arm swinging down while
another swings up. The dominant cause is judge-to-judge variance across an
independent re-run of the identical 20 cases and identical prompts — not
the catalogue change the re-run was nominally testing. **This is a finding
in its own right, more important than any single row's number**: this
eval's per-run recall/miss figures carry noise on the order of 15-25
points, which is *larger* than several of the effects this document's
"read a gap under ~10-15 points as unconvincing" guidance was calibrated
against. A single run's numbers — this one included — should be read as
one noisy draw, not a precise measurement; a claim resting on a
15-point-or-smaller difference between two arms measured in *different*
runs is not supportable from this evidence at all, only a difference
measured within the *same* run (where both arms share whatever that run's
judge-variance happened to be) comes close to comparable.

**What this does and does not change.** It does not overturn the two-hop
review result's falsification above — that verdict rested on a
pre-registered ≤57% band tested within one run (review's 54% against
control's same-run number), and the framing argument (retrospective
judge-only framing is the ceiling, not what accompanies it) is about
*mechanism*, which this re-run does not speak to either way. It does mean
future work citing this document's specific percentages should say which
run they come from and treat single-run deltas across time as unreliable;
[tools/catalogue_stats.py](../tools/catalogue_stats.py)-style regeneration
answers "did the catalogue grow", not "did routing get better or worse".

**Method note for reproducing this comparison**: the "before" row above
was obtained by `git checkout HEAD -- evals/routing/answers/` (restoring
the then-committed pre-fix answers), scoring, then restoring the fresh
answers actually being committed — not from a second live judging pass, so
it is exact, not an estimate.

## The supporting moves, now the primary recommendation

**Written as the fallback whatever the experiment said. The experiment said
54%, so this is no longer the fallback — it is the recommendation, not a
retirement path: retirement manages catalogue size, and this repo's own
plan is to scale to hundreds or thousands of practices, so shrinking the
catalogue to make one 20-case eval read better works against the stated
goal. Enforcement is the move that scales, because it does not compete for
attention at all — a checked practice is never loaded, so a 500-practice
catalogue with 500 checks costs a session nothing extra to comply with.**

**Enforce, gate, or mark advisory — every practice, not a token few.** As of
2026-09-01, after a second, more thorough pass through every remaining
practice rather than stopping at the first verdict — see
[spec/ENFORCEMENT.md](ENFORCEMENT.md) for the current, generated count):
**24 of 54 carry a real `checked_by`** (the catalogue itself grew to 53 this
session: `checkable-gets-checked`, the practice this second pass argued for
directly — see [below](#a-standing-rule-for-the-catalogues-own-growth)).
`label-describes-content`,
`acronyms-glossary`, `github-setup-disclosed` and `docs-are-current-state`
were the first four converted since this document's 54% result, each
gating only what a change adds rather than the pre-existing corpus, to
avoid the failure doc_lint's own numbers-gate opt-in already learned:
gating legacy debt fails forever and gets switched off. A second pass added
two more: **`two-check-levels`**, by making the naming decision the
practice asks for rather than treating it as blocking — AGENTS.md's
"Working in this repo" section already described a fast pre-commit lint and
a fuller pre-push suite without naming them, so the fix was naming what was
already there (**light check** = `doc_lint.py`, **deep check** = the full
gate suite), not inventing new process. And **`index-remembers-past`**,
retried with a narrower design after the first attempt's false positive
(below): it flags inline language naming what a document replaced or was
replaced by, in a changed document, with an explicit, named exemption list for
files whose stated purpose is a historical record — currently just
[the phase-2 loader spec](LOADER.md), which correctly keeps prior
measurement runs as a deliberate appendix headed "superseded by vN above."
The first version of this check had no exemption list and would have fired
on that correct usage — caught before merge, not after, the same way
`label-describes-content`'s narrower regex was caught earlier this thread.

**8 more are reached by the gate-triggered channel**
([tools/precedent_gate.py](../tools/precedent_gate.py): `capture-gate`,
`convention-to-audit`, `merge-authorization-keyword`, `merge-runbook`,
`mistakes-become-rules`, `reply-links-files`, `repo-is-memory`,
`second-pass-capture`) — deterministic reach at the moment they apply
(merge, push, reply, review), stronger than the occasion index though not
compliance-checked, because what they govern is a workflow property (did
the session do X in this thread), not a diff property a script can inspect
after the fact. `merge-authorization-keyword` was specifically evaluated
for the same treatment as `two-check-levels` — name a fixed trigger word for
this repo, then check it's documented — **and deliberately not adopted**:
unlike a check-level name, a merge-authorization keyword is a standing
grant of unattended merge authority, and inventing one unilaterally would
be a bigger decision than the practice's enforcement gap justifies making
without being asked. It stays gate-reached only, by the repo maintainer's
explicit choice, not by a check that resisted trying.

**Correction, 2026-09-01 (a later session, deep-check audit).** The "8"
above was wrong even at the moment it was written: `checkable-gets-checked`
— named two paragraphs up as this very pass's own newly-minted practice —
carries `gates: [review]` and belongs in this list too, making the
contemporaneous count 9, not 8. `todo-is-a-handoff`, converted from
`main` later the same day (see CHANGES_TO_TELL_ALEX.md), is also
gate-only (`gates: [merge]`) and brings the CURRENT total to **10**:
`capture-gate`, `checkable-gets-checked`, `convention-to-audit`,
`merge-authorization-keyword`, `merge-runbook`, `mistakes-become-rules`,
`reply-links-files`, `repo-is-memory`, `second-pass-capture`,
`todo-is-a-handoff`. Run `python3 tools/precedent_gate.py --list` for the
live list rather than trusting a count written here — this correction
itself will go stale the next time a gate-only practice is added, which
is the reason `orientation-map` and the catalogue's own generated figures
exist as scripts rather than as prose asserted once and left.

**The remaining 20 are genuinely neither**, and the honest reason splits
into two groups worth naming rather than lumping as one undifferentiated
"prose-only" count: domain-specific quantitative-document practices this
repo doesn't itself exercise (`name-both-sides-of-ledger`,
`parallel-artifact-ledger`, `permutation-frontier-column`,
`one-formatter-per-quantity`, `tabular-shared-renderer`, `quote-discipline`,
`outward-summary-discipline`, `verify-decomposition`, `pr-template-honest-gates`
— this last one specifically because it governs a pull request
*description's* honesty against the diff, which is checkable in principle but not from
this repo's local file state, since the description lives on GitHub, not
in the tree); and reasoning-quality practices with no mechanical signature
distinguishable from correct work (`affordance-is-shared`,
`build-buy-decompose`, `check-source-architecture`,
`frame-from-audience-question`, `lead-with-what-it-is`,
`layered-practice-packs`, `section-order-by-frequency`, `variant-re-derives`,
`registry-source-of-truth`). `readers-vocabulary` and
`volatile-rules-carry-dates` sit with the second group for reasons worth
stating precisely, because both were re-attempted this pass and both failed
for a checkable, demonstrated reason rather than an assumed one:
`readers-vocabulary`'s all-capital-letters half is now covered by `acronyms-glossary`,
but its jargon half has no signature short of a maintained blocklist of
"this repo's jargon," which would be an editorial call fabricated
unilaterally rather than a check, exactly the failure class phase 4's
postmortem already warned against. `volatile-rules-carry-dates` looked
tractable — check that "verified"/"as of" is followed by a date — until a
grep of this repo's own prose showed *why not*: "verified by regenerating
them," "as of this writing," and a dozen more ordinary uses of those words
with no date anywhere nearby, which a check would have flagged across
nearly every doc in the repo. Every practice should either carry a check, a
gate, or be explicitly labelled advisory, so the catalogue stops claiming a
bindingness it has not earned. [spec/ENFORCEMENT.md](ENFORCEMENT.md) has the
machinery and the honest account of which practices resisted a check and
why.

### A standing rule for the catalogue's own growth

The gap between the first enforcement pass (3 converted, ~30 called
resistant) and the second (2 more converted, one more confirmed resistant
with evidence rather than assumption) was real practices, not noise —
which means "did we actually try" is itself worth encoding as a rule
rather than trusted to whoever happens to be doing the next pass.
[`checkable-gets-checked`](../practices/checkable-gets-checked.md) is that
rule: before a new practice is left `checked_by: null`, actually attempt
the check, and don't wire one in without testing it against the whole
tree first — the second half matters as much as the first, since
`label-describes-content` and `index-remembers-past` both had a version
that fired on legitimate work before being narrowed. It fires at the
`review` gate (the same moment `cite-the-incident` and
`mistakes-become-rules` fire, and for the same reason: whether a check was
genuinely attempted, like whether a mistake is systemic, is a judgment a
review makes — no path glob reaches a moment). This is the catalogue's
53rd practice, minted fresh rather than migrated from BestPractice's
original 52, and the first to exercise that path in this repo's own
harness — which found and fixed two real gaps in the harness itself
(`check_no_invented_content` and `check_citation_integrity` both assumed
every practice file traces to a BestPractice-numbered ancestor, contrary
to what [spec/PRACTICE_FORMAT.md](PRACTICE_FORMAT.md) already said the
format should support) rather than working around them.

**Retirement is not the fix here and is deliberately not pursued as one.**
An earlier version of this section named it as a parallel option. It isn't:
this repo's own stated goal is scaling to hundreds or thousands of
practices, and shrinking the catalogue to raise a 20-case eval's score
works against that goal rather than toward it — it would be optimizing the
measurement, not the system it measures. Enforcement and gating are the
moves that scale with catalogue size instead of fighting it, because a
checked or gated practice is never competing for attention in the first
place. Retirement still has a legitimate use — a practice that turns out to
be wrong, redundant with another, or actively harmful should still be
retirable — but "the catalogue is diluted" is not that case, and is not a
reason to reach for it.

## Candidate designs for a future attempt — named, not scheduled

**Read the header on this section correctly: this is not authorization to run
another routing pass.** [The supporting moves](#the-supporting-moves-now-the-primary-recommendation)
above are the current plan — enforce more, retire what a session can't hold.
This section exists so that *if* someone later revisits the review-arm
question, they inherit a considered design instead of re-deriving one from
the same 54% that already got a verdict, and so the ideas don't quietly
bypass pre-registration by never having been written down. Any of what
follows still needs its own `PREDICTION`-style file with numeric targets and
failure criteria, committed before it runs — the same discipline every prior
run in this document followed.

### External precedent

[OpenViking](https://github.com/volcengine/OpenViking) — a context database
for AI agents (memory management, RAG, and agent-framework retrieval,
unrelated to this project) — independently arrived at a shape worth knowing
about, solving a structurally similar problem: surfacing relevant material to
an LLM without paying full-corpus cost. Its README (verified 2026-08-31)
describes a **three-tier abstraction**, loaded on demand: **L0** (~100-token
one-sentence summary, for rapid relevance triage), **L1** (~2k-token
overview, for planning), **L2** (full original content, loaded only when
needed) — plus directory-based hierarchical drill-down (vector search finds
the highest-scoring directory, then descends layer by layer so results carry
their surrounding context) and an observable retrieval trajectory (every
query records which path produced its result, for debugging). Stated
figures: 34–91% token reduction at 80–83% accuracy against a full-load
baseline, benchmarked against Doubao models.

**What the README does not say, checked rather than assumed**, since citing
this fairly means being honest about its gaps: it does not disclose what
triggers L0→L1 or L1→L2 expansion (relevance threshold, agent judgment, or a
fixed policy — undetailed), it does not describe any tagging or metadata
layer on content items (retrieval is vector search over directory structure,
not tags), and its benchmark methodology lives behind a blog post this
session's network could not reach (`blog.openviking.ai` is egress-blocked
here). So it is independent validation of *the tiering principle* — a middle
abstraction between "one-line clause" and "full text" measurably helps
elsewhere on a related problem — not a source of mechanism to import
wholesale. Treat the 80–83%/34–91% figures as someone else's number on a
different task, not as evidence bearing on this repo's 20 cases.

### Three ideas, connected to the diagnosis above

Raised in conversation after the 54% result, checked against what the
[case-level diagnosis](#why-it-landed-below-the-loaders-own-working-session-recall-not-just-below-control)
above actually found — the review arm's misses were not, mostly, judgment
failures on content it saw; they were practices it never got more than an
80-character occasion-index clause on.

1. **~~A middle "gloss" tier per practice~~ — tried, falsified.** Between the
   occasion index's 80-char clause ([spec/PRACTICE_FORMAT.md](PRACTICE_FORMAT.md))
   and the full Rule, structurally OpenViking's L1. This was the most
   directly motivated of the three: c07 missed `layered-practice-packs`,
   `registry-source-of-truth` and `readers-vocabulary` specifically because a
   clause was all it ever saw of them. Pre-registered as
   [evals/routing/PREDICTION_GLOSS_TIER.md](../evals/routing/PREDICTION_GLOSS_TIER.md)
   and run: **53.7% recall, inside the pre-registered no-effect band, at
   nearly double the review arm's token cost.** See
   [the gloss-tier result](#the-gloss-tier-result-2026-09-01). Left here,
   struck through rather than deleted, so nobody re-derives and re-runs the
   same idea from scratch.
2. **~~More budget for the judge pass specifically, via a real second hop~~
   — tried, falsified, harder than idea 1.** The resident budget
   (`RESIDENT_BUDGET_TOKENS = 2000` in [tools/build_views.py](../tools/build_views.py))
   is genuinely zero-sum, and lengthening resident text was already tried
   once (the Rule/Detail split, v2→v3) with an effect inside this eval's own
   noise floor — so the proposal was to spend the review arm's token
   headroom on a genuine two-hop version (open-on-request, like treatment's
   hop 2) instead. Pre-registered as
   [evals/routing/PREDICTION_TWO_HOP_REVIEW.md](../evals/routing/PREDICTION_TWO_HOP_REVIEW.md)
   and run: **50.5% recall — the lowest of the three retrospective-framing
   arms tried, at control-level token cost.** See
   [the two-hop review result](#the-two-hop-review-result-2026-09-01). Left
   here, struck through, for the same reason as idea 1.
3. **Persistent tagging of practices *and* the cases being judged — now
   predicted null on stronger grounds than when this was written.** A
   semantic upgrade to literal path-glob matching, worth trying, per this
   entry's original text, only as the retrieval mechanism *feeding* idea 1
   or 2 (a tag-based prefilter paired with something that gets fuller text
   in front of the judge) rather than standalone — but idea 1 and idea 2 are
   now both tried and both falsified, at 53.7% and 50.5% respectively,
   inside noise of the untagged review arm's 54%. The
   [two-hop result](#the-two-hop-review-result-2026-09-01) narrows this
   further than the original reasoning did: the constraint on this eval was
   never *what got surfaced* (both idea 1 and idea 2 changed that, in
   different ways, and neither moved the number) — it was the
   retrospective, judge-only framing every arm sharing this discussion has
   used. A tagging-based prefilter changes only what reaches the judge, so
   on the evidence now on record it inherits the same ceiling regardless of
   which channel (glob, gloss, tag) does the surfacing. Still untested in
   the literal sense — nobody has run it — but the reason to expect a null
   result no longer rests only on the v3–v5 routing-pass precedent; it rests
   on two direct falsifications of the two mechanisms it was proposed to
   pair with.

## What would change my mind

Recorded so the next session can disagree with this document on evidence
rather than by preference. The first of these fired:

- **The review arm lands at 77%.** ✅ **It landed at 54%, which is the same
  outcome in a stronger form.** Framing is not the lever, the loader's
  context is, and the recommendation above collapses to "enforce more, carry
  less" — see [The review-arm result](#the-review-arm-result-2026-08-31).
- **A human spot-check finds the oracle is wrong often.** The 16-point gap is
  measured against a model's judgment sharing the oracle's context shape. The
  plan flagged this limit at phase 2 and it has never been checked. If the
  oracle over-lists, some of the control's "misses" are the control being
  right.
- **The 20 cases are unrepresentative.** They are all from this repository's
  own history, and they are unusually practice-heavy — most of them are
  commits that write or change rules. A case set drawn from ordinary
  application work might behave differently.

## Does the ceiling reach Stage 1 and Stage 3? (2026-09-02, reasoned not measured)

[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) flags, right before
Stage 1, that this document's finding might undercut two pieces of the
creation pipeline: Stage 1's "session judgment at a gate" and Stage 3's
promotion criteria (recurrence, non-duplication) both ask a session to judge
something against the existing catalogue, which is the same verb this
document spent six runs measuring. The plan calls this "not yet resolved
either way" and asks for the reasoning to happen before Stage 1 is built,
not after. This section is that reasoning, done in writing rather than
skipped — and, per its own header, reasoned rather than measured, so treat
it as an argument to disagree with on evidence, the same invitation the rest
of this document extends.

**The measured ceiling is about one shape of task, and Stage 1/3 are a
different shape.** Every arm in this document's six runs asks a session to
sweep the **whole catalogue** against a **whole finished diff** in **one
pass**, retrospectively: "which of these 52-to-54 practices apply to this
change?" The case-level diagnosis of the 54% result found the actual failure
mode was never getting more than an 80-character occasion-index clause on
most candidates before having to render a verdict — an attention problem
created by breadth (many candidates, thin evidence per candidate, one
judgment covering all of them). Stage 1 and Stage 3 do not have that shape:

- **Stage 1's gate judgment** looks at **one candidate at a time**, each
  with its own attached evidence (a commit, a quote, a failing check) rather
  than an 80-character clause, and answers a narrower question than "does
  this apply" — closer to "is this worth writing down as a candidate,"
  which costs nothing to get wrong in either direction (Stage 2: "creating
  one costs nothing; ignoring one costs nothing").
- **Stage 3's non-duplication check** is a **query** — does an existing
  slug or text already cover this — not a sweep of judgment over the full
  catalogue. Its recurrence check is a **count** over dated candidate
  records, not a retrospective judgment call at all.

Both are structurally closer to the **oracle's** framing (one item, its own
evidence, a closed question) than to the **review arm's** (54 items, one
clause each, one pass) — and the oracle is the only arm in six runs that
does not sit at 50–54%. That is not evidence Stage 1/3 will score like the
oracle; it is a reason to expect they are not the same task this document
falsified three times, which is what "not yet resolved" was actually asking
for.

**Why this is not measured before building, and why that is the right call
here rather than a shortcut.** This document's own closing discipline
(["do not re-run any of them to see if the number
moves"](#for-the-session-that-picks-this-up)) is about re-testing the
*same* framing hoping for a different result. Stage 1/3 is not that — it is
an untested framing, and pre-registering a fourth eval arm for a pipeline
that does not exist yet, to decide whether to build it, spends a full
measurement cycle to de-risk a task shape nobody has exercised even once.
The cheaper, honest sequencing is to build Stage 1–3 on the reasoning above,
stated plainly as reasoning rather than dressed as a finding, and let Stage
6 close the loop: **the retirement report already asks "did this fire, was
this cited"** for every promoted practice, which is a real, low-cost place
to check — once there is a population of Stage-1/3 decisions to check
against — whether a gate's or a promotion's judgment call agreed with what
actually happened. If that later comparison goes badly, *that* is the
measured result this section does not have, and revisits this reasoning on
its own terms rather than on precedent from a differently-shaped eval.

## For the session that picks this up

**Three experiments in this line have now been run; do not re-run any of
them to see if the number moves.** Review (one hop, clause only): 54%.
Review-gloss (one hop, clause+gloss): 53.7%
([result](#the-gloss-tier-result-2026-09-01)). Review-hop2 (two hop, full
Rule on request, still judge-only and retrospective): 50.5%
([result](#the-two-hop-review-result-2026-09-01)) — the lowest of the
three, at control-level token cost. **All three cluster at 50–54% while the
two prospective-framing arms (control 84%, treatment 77%) sit 23–34 points
higher on the same cases, same oracle.** Read plainly: judge-only,
retrospective framing has a ceiling around 54% on this eval, and nothing
tried so far that keeps that framing — more text, more choice — moves it.
Idea 3 (tagging) was never separately run but is now predicted null on
direct evidence rather than precedent alone, since it would only change
what reaches a judge already shown to be capped by its framing, not its
content — see its entry in [Candidate designs](#candidate-designs-for-a-future-attempt--named-not-scheduled).

**There is no candidate design left in this document that has not been
either run and falsified, or predicted null on falsified siblings' direct
evidence.** [The supporting moves](#the-supporting-moves-now-the-primary-recommendation)
have already been pushed as far as they honestly go for now: **24 enforced,
10 more gate-only (see the 2026-09-01 correction above), 20 genuinely
resistant**, each of the 20 broken down by *why* in that section — not a stopping point chosen
for convenience, but a second full pass through every remaining practice
that converted two more (`two-check-levels`, `index-remembers-past`) and
demonstrated, rather than assumed, why the rest resist (`volatile-rules-carry-dates`
specifically retried and shown false-positive-prone by grepping this
repo's own prose). Not retirement, which this document no longer
recommends: it manages catalogue size against a goal (scaling to hundreds
or thousands of practices) that retirement works against, not toward. If review-as-primary-control is ever revisited, it needs a framing
genuinely different from "judge a finished diff, retrospectively" — not a
fourth variant of context or choice within that framing — and it needs its
own pre-registration stating why this document's three results don't
already predict its outcome, not a claim that this run's gloss or hop-count
was tuned wrong.

The tree is at `precedent-beta-v01`. Working rules are in
[spec/PHASE3_BRIEF.md](PHASE3_BRIEF.md) and
[AGENTS.md](../AGENTS.md)'s gotchas section; the short version:

- Three gates after every change: `python3 tools/verify_harness.py`
  (0 failed is what matters — the passed/N-A counts grow as checks are
  added, so a hardcoded figure here goes stale by design; this document
  had one and a 2026-09-01 deep-check audit found it already wrong),
  `python3 tools/doc_lint.py`, `python3 tools/leak_gate.py`. Also
  `python3 tools/precedent_check.py` (0 violated is what matters, same
  reason) and `python3 tools/doc_sync.py`.
- The vocabulary layer needs `PRECEDENT_LEAK_BLOCKLIST` pointing at a
  blocklist **outside** the repo plus
  `git config precedent.requireVocabulary true`, or it fails open.
- Never read a `practices/*.md` file directly — `tools/precedent_show.py`.
- The generated views are generated: `tools/build_views.py`.
- Never `main`. Never amend a pushed commit.
