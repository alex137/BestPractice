<!-- Last updated: 2026-09-04 (session responding to Morgan's direct request) -->

# Pre-registered prediction for the two new audit mechanisms' judgment quality

**Written before any seeded case was judged.** Covers both
[full-practice-audit](../../practices/full-practice-audit.md)'s whole-sweep
and [routing-audit](../../practices/routing-audit.md)'s rotating deep-read
slice, because they share the identical judgment mechanism —
[tools/full_practice_audit.py](../../tools/full_practice_audit.py) hands a
judgment-only practice's full Rule text to the invoking session and asks a
closed, one-at-a-time question; `tools/routing_audit.py slice` does the same
against a smaller rotating subset. Evaluating one evaluates the mechanism
both tools share; the coverage() half of `routing-audit` is separately
mechanical and is not a judgment question — that half is now a planted case
in `tools/verify_harness.py` (`check_routing_audit_coverage`), added in this
same session, not part of this document.

## Why this harness shape, not evals/routing/'s existing one

[spec/UNBUILT_PLAN_ITEMS.md](../../spec/UNBUILT_PLAN_ITEMS.md) (Part 2) asks
explicitly to decide and state the harness shape rather than force a fit,
because `full-practice-audit` is not diff-scoped: it sweeps the whole
catalogue against the whole repo state, not a case's changed files. The
existing `evals/routing/cases.json` / `tools/routing_eval.py` machinery is
built around 20 diff-shaped cases with a pre-scored oracle and does not
apply here without a different kind of ground truth.

**What this run uses instead: seeded violations, judged blind.** Six
judgment-only practices from the current universal catalogue, each given a
closed-question verdict — *does it apply; if it applies, is it satisfied* —
by a fresh session with no memory of this conversation, run inside an
isolated `git worktree` (never touching the working tree Morgan sees, never
committed to a real branch). Three practices carry a real, deliberately
seeded violation added to the worktree only:

| slug | seeded artifact | how it violates |
|---|---|---|
| `registry-source-of-truth` | `spec/audit_eval_seed/registry_note.md` | hardcodes "24 of 54 practices... enforced" as a duplicated status figure instead of deriving it from `tools/precedent_gate.py --list` / `tools/full_practice_audit.py` |
| `volatile-rules-carry-dates` | `spec/audit_eval_seed/deploy_note.md` | asserts external-platform (GitHub Actions) behavior with no `as of <date>` / `verified <date>` |
| `lead-with-what-it-is` | `spec/audit_eval_seed/new_mechanism_intro.md` | opens with the document's own edit/review process before saying what the audit tools are |

Three practices are judged in their real, unmodified state, with ground
truth established by inspection before this file was committed, disclosed
here rather than assumed: `check-source-architecture` and
`build-buy-decompose` (both narrow-trigger; `grep`-confirmed no
trade-study or build/buy decision content exists anywhere in this repo
outside the practices' own definitions, so the correct verdict is
"not applicable") and `one-formatter-per-quantity` (already named by
[spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md) as one of the
domain-specific practices "this repo doesn't itself exercise" — an
existing, independent finding reused as ground truth rather than
re-derived).

**Ground truth**, stated as the binary the judge is scored against —
`should_flag`:

| slug | should_flag | why |
|---|---|---|
| `registry-source-of-truth` | **true** | seeded |
| `volatile-rules-carry-dates` | **true** | seeded |
| `lead-with-what-it-is` | **true** | seeded |
| `check-source-architecture` | **false** | not applicable (checked) |
| `build-buy-decompose` | **false** | not applicable (checked) |
| `one-formatter-per-quantity` | **false** | not applicable (per ATTENTION_CEILING.md) |

## The prediction

**Point prediction: 5 or 6 of 6 correct (≥83%).** Unlike the review arm
[spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md) measured at
54%, this mechanism does not share the review arm's specific, diagnosed
failure mode — an 80-character occasion-index clause standing in for a
practice the judge never got more than a glance at. Both new tools hand the
judge the practice's **full Rule text**, one practice at a time, with the
**actual current repo state** available to inspect (not a frozen diff
snapshot) — structurally closer to the **oracle's** framing (full context,
one item, closed question) than to the falsified review arm's (54 items,
one clause each, one pass). [The reasoning ATTENTION_CEILING.md gives for
Stage 1/3](../../spec/ATTENTION_CEILING.md#does-the-ceiling-reach-stage-1-and-stage-3-2026-09-02-reasoned-not-measured)
applies here almost unchanged: this is "one candidate at a time, each with
its own attached evidence," not "54 items, one clause each, one pass" — and
a 6-case, closed, evidence-attached run is exactly the kind of *test* of
that reasoning the plan asked for but had not yet run, not a restatement of
it.

## Failure / unconvincing criteria — read before the number, not after

- **4 of 6 or fewer correct (≤67%)** falsifies the prediction that
  full-Rule, one-at-a-time, evidence-attached judgment escapes the review
  arm's ceiling. That would be the more important finding of the two
  possible outcomes: it would mean the review arm's 54% was not really
  about clause-thinness, and the Stage 1/3 reasoning above needs
  re-examination on real evidence rather than staying "reasoned, not
  measured."
- **N=6 is small — deliberately, for a single-session turn budget — and a
  single run.** This is not the routing eval's 20-case, multi-run, noise-
  floor-calibrated discipline; treat any result here as a first, coarse
  signal, not a replacement for that rigor if the finding turns out to
  matter enough to invest a full multi-session evaluation in later. Report
  the raw per-case verdicts, not just the score, so a later session can see
  exactly which of the 6 it agreed or disagreed with.
- **A "false" verdict on a seeded-violation case must be checked for cause
  before being counted as a plain miss**: did the judge fail to find the
  seed file at all (a real practical gap — the tool prints the Rule but the
  session still has to think to inspect `spec/audit_eval_seed/`, the same
  way any repo file would need discovering), or did it find the file and
  reason the content was fine (a judgment failure proper)? Report which,
  per case, in the write-up — they are different findings.
- **This run does not evaluate `routing-audit`'s coverage() half or its
  rotating-slice selection logic (which practices come up, in what order)**
  — only the judgment applied once a practice is in front of the session,
  which is the part the two tools share.

## Method

- Seeded in an isolated `git worktree` off the current `precedent-beta-v01`
  HEAD, on a throwaway branch, never pushed and removed after scoring.
- The judge is a freshly spawned agent with no memory of this conversation
  or of writing this document, given only: the worktree path, instructions
  to run `python3 tools/full_practice_audit.py`, and to judge each of the
  21 judgment-only practices it prints — closed question, one at a time,
  per the tool's own final instruction — reporting a verdict and citation
  for each. Only the 6 named above are scored against pre-registered ground
  truth; the rest are read output, not part of this measurement.
- The three seed files are written as plausible repo prose, not labeled as
  test fixtures, so the judge is not cued.
- Reported in [spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md)
  as a new, dated section — appended, not rewriting the existing three
  results — whatever this run shows.
