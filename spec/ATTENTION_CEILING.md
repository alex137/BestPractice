<!-- Last updated: 2026-08-31 (Buenos Aires) by the phase-4 build session -->

# The Attention Ceiling — What Three Runs Measured, and What To Do About It

Written for the session that takes this on next. It carries a finding, a
recommendation, and one experiment that should be run before anything is
built. Read it in full; it is short and it changes what the next phase is for.

**The one-sentence version:** the routing eval's miss rate is mostly not a
loading problem, the loader is already within noise of the best any routing
architecture can do, and the largest measured effect in the whole eval is one
nothing in the design currently exploits.

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

## The supporting moves, whatever the experiment says

**Enforce or mark advisory.** 34 of 52 practices are prose-only, and three
runs now say prose-only does not produce compliance at any catalogue size
through any channel. Every practice should either carry a check or be
explicitly labelled advisory, so the catalogue stops claiming a bindingness it
has not earned. [spec/ENFORCEMENT.md](ENFORCEMENT.md) has the machinery and
the honest account of which practices resisted a check and why.

**Exercise the retirement path.** The plan says practices must be able to die
and nothing has ever died. 52 may simply be more than a session can hold, and
the honest fix for a diluted catalogue is a smaller one. This has never been
tried and it is cheap to try.

## What would change my mind

Recorded so the next session can disagree with this document on evidence
rather than by preference:

- **The review arm lands at 77%.** Then framing is not the lever, the loader's
  context is, and the whole recommendation above collapses to "enforce more,
  carry less".
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
