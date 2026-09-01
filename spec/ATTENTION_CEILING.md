<!-- Last updated: 2026-08-31 (Buenos Aires) by the review-arm experiment session, with a candidate-design addendum from the same session's follow-up -->

# The Attention Ceiling — What Four Runs Measured, and What To Do About It

Written for the session that takes this on next. It carries a finding, the
recommendation that finding argued for, the experiment that tested the
recommendation, and the result: **the experiment falsified it.** Read it in
full; it is short and it changes what the next phase is for.

**The one-sentence version:** the routing eval's miss rate is mostly not a
loading problem, the loader is already within noise of the best any routing
architecture can do, the largest measured effect in the whole eval (framing)
looked like an opportunity — and testing it, cheaply, before building
anything, is exactly what showed it is not one: the review arm scored **54%**,
below even the loader's own working-session recall of 77%. See
[The review-arm result](#the-review-arm-result-2026-08-31) below.

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

## The supporting moves, now the primary recommendation

**Written as the fallback whatever the experiment said. The experiment said
54%, so this is no longer the fallback — it is what to do next.**

**Enforce or mark advisory.** 33 of 52 practices are prose-only (as of
2026-09-01; see [spec/ENFORCEMENT.md](ENFORCEMENT.md) for the current,
generated count — `label-describes-content` is the first one converted since
this document's 54% result, a mechanical check for a claimed length label
matching the content under it), and three runs now say prose-only does not
produce compliance at any catalogue size through any channel. Every practice
should either carry a check or be explicitly labelled advisory, so the
catalogue stops claiming a bindingness it has not earned.
[spec/ENFORCEMENT.md](ENFORCEMENT.md) has the machinery and the honest
account of which practices resisted a check and why.

**Exercise the retirement path.** The plan says practices must be able to die
and nothing has ever died. 52 may simply be more than a session can hold, and
the honest fix for a diluted catalogue is a smaller one. This has never been
tried and it is cheap to try.

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

1. **A middle "gloss" tier per practice**, between the occasion index's
   80-char clause ([spec/PRACTICE_FORMAT.md](PRACTICE_FORMAT.md)) and the full Rule — structurally
   OpenViking's L1. This is the most directly motivated of the three: c07
   missed `layered-practice-packs`, `registry-source-of-truth` and
   `readers-vocabulary` specifically because a clause was all it ever saw of
   them. To stay on the right side of "do not tune the occasion index to move
   a number," this has to be authored once per practice from the practice
   text itself, as a format change applying uniformly, not hand-fitted to
   what the 20 cases missed.
2. **More budget for the judge pass specifically, not the resident tier.**
   The resident budget (`RESIDENT_BUDGET_TOKENS = 2000` in
   [tools/build_views.py](../tools/build_views.py)) is genuinely zero-sum — a 7th resident practice
   means demoting one of the current six — and lengthening resident text was
   already tried once (the Rule/Detail split, v2→v3) with an effect inside
   this eval's own noise floor. The review arm, by contrast, is running 48%
   below control's token cost; there is headroom to spend on a genuine
   two-hop version (open-on-request, like treatment's hop 2) before losing
   the loader's cost advantage. This is functionally the same fix as idea 1,
   through a different door — either could close the gap the diagnosis
   found, and running them separately would say which one actually did.
3. **Persistent tagging of practices *and* the cases being judged**, as a
   semantic upgrade to literal path-glob matching. Checked against OpenViking
   rather than assumed to be validated by it: its README describes no
   tagging or metadata layer at all — its retrieval is vector search over
   directory structure, not tags — so this idea is not the thing OpenViking
   demonstrates; it remains a genuinely untested proposal here. It should
   also be read against this repo's own history: three routing passes (v3
   residency, v4 glob fix, v5 catalogue-wide glob pass) each improved *reach*
   and each left the total miss count unmoved — better reach converted
   never-shown misses into shown-and-declined misses without shrinking the
   total. The predicted fate of tagging alone, on that precedent, is the
   same null result. It is worth trying only as the retrieval mechanism
   *feeding* idea 1 or 2 — better candidate selection paired with something
   that actually gets fuller text in front of the judge — not as a
   standalone bet that reach was the constraint after all.

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

## For the session that picks this up

**The experiment named above has been run; do not re-run it to see if the
number moves.** Next up is [the supporting moves](#the-supporting-moves-now-the-primary-recommendation) —
enforcing more of the 34 prose-only practices, and actually trying the
retirement path — not another routing pass and not a rebuilt review arm
chasing a better score than 54%. If a two-hop review arm, a gloss tier, or a
tagging-based prefilter is ever tried, [Candidate designs for a future
attempt](#candidate-designs-for-a-future-attempt--named-not-scheduled) above
has the considered starting point and the reasoning behind each — read it
before designing from scratch, and it still needs its own pre-registration,
stated as a genuinely new experiment, not a second attempt at this one.

The tree is at `precedent-beta-v01`. Working rules are in
[spec/PHASE3_BRIEF.md](PHASE3_BRIEF.md) and
[AGENTS.md](../AGENTS.md)'s gotchas section; the short version:

- Three gates after every change: `python3 tools/verify_harness.py` (expect 28
  passed / 0 failed / 0 N/A), `python3 tools/doc_lint.py`,
  `python3 tools/leak_gate.py`. Also `python3 tools/precedent_check.py`
  (13 passed / 0 violated / 3 skipped) and `python3 tools/doc_sync.py`.
- The vocabulary layer needs `PRECEDENT_LEAK_BLOCKLIST` pointing at a
  blocklist **outside** the repo plus
  `git config precedent.requireVocabulary true`, or it fails open.
- Never read a `practices/*.md` file directly — `tools/precedent_show.py`.
- The generated views are generated: `tools/build_views.py`.
- Never `main`. Never amend a pushed commit.
