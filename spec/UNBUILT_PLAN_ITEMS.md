<!-- Last updated: 2026-09-03 (Buenos Aires) by the full-practice-audit / routing-audit session -->

# Unbuilt Plan Items — What Else the Plan Approved and the Tree Doesn't Show

This document exists because of one concrete miss, found by accident rather
than by process: [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)
approved the **routing audit** for phase 5 in its 2026-09-01 preflight
review ("v28... the unbuilt one is renamed *routing audit*"; see also "The
Routing Audit Checks Coverage, Not Content"), and nothing built it. Not
partially — nothing. It wasn't in [TODO.md](../TODO.md). It wasn't carried
forward as an open item in [spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md) or
[spec/PHASE5_DEEPCHECK.md](PHASE5_DEEPCHECK.md), both of which did
substantial phase-5 scoping and review work without mentioning it. It
surfaced only because a 2026-09-03 session, asked by a human to build a
related, newly-requested audit mechanism ("full practice audit"), read the
plan in full first rather than building from memory of the conversation
alone, and happened to notice the naming-collision entry that named it.

That session built [routing-audit](../practices/routing-audit.md) (the
approved-but-unbuilt mechanism itself) and
[full-practice-audit](../practices/full-practice-audit.md) (the new,
human-requested one) in the same sitting, and captured this document as the
follow-on it could not also do in that sitting — per
[capture-gate](../practices/capture-gate.md), captured here, now, rather than
parked for a review that might not happen. Two pieces of real work are
queued here, both **out-of-scope** for that session (large, and needing room
this session did not have left): investigating the gap itself, and properly
evaluating the two mechanisms it built before their output should be
trusted. See [TODO.md](../TODO.md) for the tracked entry pointing here.

## Part 1 — Why did routing audit fall through, and what else did?

**The question.** A plan-of-record deliverable, explicitly approved in a
dated decision, went unbuilt and unlogged for roughly two days across
several phase-5 and phase-6 working sessions, each of which read
`PRACTICE_ENGINE_PLAN.md` per the standing instruction at the top of
[AGENTS.md](../AGENTS.md) ("read PRACTICE_ENGINE_PLAN.md first, in full").
Reading it clearly was not the failure — the entry that names routing audit
is a normal amendment paragraph, not buried or malformed. What's worth
root-causing:

- Did `spec/PHASE5_BRIEF.md` deliberately scope routing audit *out* of
  phase 5 for a stated reason, and that reason simply never made it into
  this document or `TODO.md`? Read that brief's own "what phase 5 covers"
  framing first, rather than assuming silence means an oversight.
- Or was it a genuine drop — approved, in scope, and lost between the
  preflight decision and the actual phase-5 build list? If so, what about
  the workflow let that happen (a plan amendment that isn't also a `TODO.md`
  line item has no second place it's tracked from) — and does
  [todo-is-a-handoff](../practices/todo-is-a-handoff.md)'s own discipline
  (queue only with a stated reason) actually get followed for
  plan-approval-level commitments, or only for smaller open items?

**The method.** Don't take this document's framing as the full inventory —
it names one confirmed gap, not a completed audit. Grep
`PRACTICE_ENGINE_PLAN.md` for its own forward-looking commitments: "to
build", "still to build", "not yet built", "not yet inventoried",
"deferred", the Sequence table's row-by-row done-when conditions, and any
phase's own named deliverables. Cross-reference each hit against what
actually exists in `tools/`, `practices/`, `spec/`, and `TODO.md`, and
against the phase briefs
([spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md), [spec/PHASE5_DEEPCHECK.md](PHASE5_DEEPCHECK.md),
[spec/PHASE6_BRIEF.md](PHASE6_BRIEF.md)) to see whether each was logged as
done, deferred with a reason, or silently dropped like routing audit was.
Build a table — one row per approved item, its build status, and where (if
anywhere) that status is disclosed — the same shape
[spec/PREFORK_AUDIT.md](PREFORK_AUDIT.md) already used for the inherited
catalogue, applied here to the plan's own forward commitments instead.
Fold confirmed gaps into `TODO.md` with a real blocked-on/out-of-scope
reason each, per `todo-is-a-handoff`; a plan-approved item that turns out
to have been correctly and disclosedly deferred needs no new entry, only a
note here that it was checked.

**Also worth naming plainly, not just implying:** if this audit turns up a
second silent drop, the finding is not "fix that one item" — it's that
plan-approval alone does not reliably survive into the build list, which is
a process gap bigger than any one missing tool.

## Part 2 — Pre-register and run a real evaluation of both new mechanisms

Neither [routing-audit](../practices/routing-audit.md)'s rotating deep-read
slice nor [full-practice-audit](../practices/full-practice-audit.md)'s
whole-catalogue sweep has been measured. Both practice files disclose this
honestly and cite [spec/ATTENTION_CEILING.md](ATTENTION_CEILING.md)'s
review-arm result (54% recall, worse than no review at all) as the reason
their reliability should not be assumed. That document's own closing
section is explicit and should be read before this work starts:

> "There is no candidate design left in this document that has not been
> either run and falsified, or predicted null on falsified siblings' direct
> evidence... If review-as-primary-control is ever revisited, it needs a
> framing genuinely different from 'judge a finished diff, retrospectively'
> — not a fourth variant of context or choice within that framing — and it
> needs its own pre-registration stating why this document's three results
> don't already predict its outcome."

Both new mechanisms have to clear that bar before being trusted, not be
built on the assumption they already do:

- **`full-practice-audit`** is arguably NOT a fourth variant of the same
  framing — it removes the loader-prefilter step the three falsified runs
  all shared (control, treatment, and the review arm itself all worked from
  loader output; this reads the whole catalogue directly) and it changes
  the unit of judgment (closed yes/no per practice, per this practice's own
  Rule, rather than one open "which of these applied" question). Whether
  that's a real enough difference to justify a fresh run, or just a bigger,
  slower version of the same falsified shape, is exactly the question a
  pre-registration has to answer honestly before running anything — argue
  it in writing first, the same discipline `evals/routing/PREDICTION_REVIEW_ARM.md`
  and its siblings already model.
- **`routing-audit`'s rotating slice** is smaller in scope per run (a
  bounded N, not the whole judgment-only set) and is closer in spirit to
  the "closed questions, one practice at a time" design
  `spec/ATTENTION_CEILING.md`'s own recommendation named but explicitly
  never ran ("The second experiment... did not[validate], so... it is not
  run"). That makes it a plausible candidate for the retry that document
  left open — argued for directly, not assumed, in its own
  pre-registration.

**Concretely, for the session that picks this up:**

1. Read `spec/ATTENTION_CEILING.md` in full — not just the excerpt above —
   before writing anything. Cases, oracle, and cost data already exist in
   `evals/routing/` (`cases.json`, `answers-v*/`); [tools/routing_eval.py](../tools/routing_eval.py)
   is the existing harness that ran the three falsified arms. Whether it
   fits either new mechanism unmodified is a real open design question —
   `routing-audit`'s slice is diff-scoped like the existing arms, but
   `full-practice-audit` is not diff-scoped at all (it reads the whole
   catalogue regardless of what changed), so it may need a differently
   shaped harness. Decide and state which, in the prediction document
   itself, rather than silently forcing a fit.
2. Write a `PREDICTION_*.md` document per mechanism, in `evals/routing/`,
   before running anything against real cases — stating the threshold that
   falsifies it, in advance, the same discipline every prior run in this
   line used.
3. Run it once, report the result in `spec/ATTENTION_CEILING.md` (a new
   dated section, appended — never rewriting the existing results) or a new
   sibling document, whichever the result's shape actually calls for.
4. If either mechanism is falsified the same way the review arm was, that
   is not a reason to hide the tool — both are already disclosed,
   on-demand, backstop-only, explicitly not the primary control. It is a
   reason to say so plainly in the practice file's own `## Why`, the same
   honesty this repository already asks of `spec/ATTENTION_CEILING.md`
   itself.
