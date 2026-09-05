<!-- Last updated: 2026-09-04 (Buenos Aires) by the session that answered Part 1 and pre-registered Part 2 -->

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

## Part 1, answered (2026-09-04)

**Root cause: a genuine drop, not a deliberate scoping-out — and it
happened one specific way, not by carelessness.**
[`PRACTICE_ENGINE_PLAN.md`'s v28 amendment](../PRACTICE_ENGINE_PLAN.md#amendments-since-approval)
(2026-09-01) named routing audit "still to build in phase 5" in the prose
of ["The Routing Audit Checks Coverage, Not
Content"](../PRACTICE_ENGINE_PLAN.md#the-routing-audit-checks-coverage-not-content)
— but the *same pass's* own
["What phase 5 should carry forward"](../PRACTICE_ENGINE_PLAN.md#what-phase-5-should-carry-forward)
section, written immediately after, never mentions it, and neither does the
top-level [Sequence table](../PRACTICE_ENGINE_PLAN.md#sequence)'s phase-5
row ("Done when": candidates, detection, promotion, approval routing, the
retirement report — no routing audit). Those two sections are the
checklists a downstream session actually works from — confirmed by reading
[spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)'s own "what phase 5 covers"
framing, which never mentions routing audit either way (not a stated
exclusion, a genuine absence) — while the naming-fix prose sits several
hundred lines earlier, in an architecture section, not a checklist.
[spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md) (2026-09-02),
[spec/PHASE5_DEEPCHECK.md](PHASE5_DEEPCHECK.md) (2026-09-02) and
[spec/PHASE6_BRIEF.md](PHASE6_BRIEF.md) (2026-09-03) each read the plan per
`AGENTS.md`'s standing instruction and correctly worked from the
carry-forward/Sequence checklists rather than re-deriving a build list by
re-reading the whole plan's prose for commitments — which is the rational
way to work from a document `AGENTS.md` itself says not to hold entirely in
context at once. **The mechanism is structural, not a lapse: a v-numbered
amendment has no required second write into the checklist a downstream
session actually consults, so an approval that lives only in prose is
invisible to the method every subsequent session correctly used.**
`todo-is-a-handoff`'s discipline (queue only with a stated reason) was not
violated so much as never invoked — the amendment was implicitly treated
as self-tracking ("it's written down, so it will be seen") when the plan's
own working method guarantees the opposite for anything not also mirrored
into `TODO.md` or a phase's own carry-forward note.

**The scan for other drops** (method: grep the plan for "to build", "still
to build", "not yet built", "not yet inventoried", "deferred"; check every
phase's Sequence done-when row; check the only two other blockquote-style
"amended" callouts in the document) found no second live gap of the same
shape, and two adjacent cases worth recording rather than re-deriving later:

- **The gate-triggered channel** ("still unbuilt" at the time of the
  routing-eval-recall section, [PRACTICE_ENGINE_PLAN.md line
  1136](../PRACTICE_ENGINE_PLAN.md)) was never logged in any carry-forward
  section either — but it got built anyway
  ([tools/precedent_gate.py](../tools/precedent_gate.py), 10 gate-only
  practices as of [spec/ATTENTION_CEILING.md](ATTENTION_CEILING.md)'s
  2026-09-03 correction). A second near-miss of the identical shape that
  happened not to cost anything. Not actioned further; recorded so the next
  audit of this kind does not re-discover it from zero.
- **The RPP "very deep check" audit list**
  ([PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md), the same v28
  naming-fix callout: "Not yet inventoried here (RPP is a separate private
  repo); enumerate and wire it as an on-demand tool when phase 5 or later
  actually needs it") is genuinely still not inventoried or wired —
  confirmed by grep: zero hits anywhere in the tree outside the plan
  itself, and one passing mention in
  [tools/full_practice_audit.py](../tools/full_practice_audit.py)'s own
  docstring naming `full-practice-audit` its "closest existing analog,"
  which nobody had connected back to this specific unmet commitment.
  Unlike routing audit, this deferral was conditional ("when... actually
  needs it") rather than phase-bound, so it is arguably still correctly
  pending rather than dropped — but it carries the identical structural
  risk (a real, named commitment tracked nowhere but the plan's own prose)
  and has now sat through the entirety of phases 5 and 6-so-far with nobody
  weighing whether the condition has since been met. Given a second place
  to be tracked from **is** the fix this investigation argues for, it is
  added as `TODO.md` item 14 now rather than left to be found by accident a
  second time.
- The plan's only other blockquote-style "amended" callout (Phase 2,
  "Superseded in part, 2026-08-31") correctly points to its own
  replacement section and introduces no untracked commitment.
  `in_repos:`/team-scoped individual practices sits in an explicitly named
  "Deferred (speculative — do not build yet)" section — disclosed by its
  own heading, not a silent drop.

**The generalized finding, stated as plainly as the original question
asked for:** plan-approval alone does not reliably survive into the build
list. The fix demonstrated here is not "read more carefully" — every
session that missed this read carefully — it is that a v-numbered amendment
introducing a "still to build" commitment needs a `TODO.md` line (or a
carry-forward-section edit) in the same commit that writes the amendment,
not only when a later session notices the gap by accident, as this one did.

### The RPP "very deep check" list, resolved (2026-09-05)

A session holding
[RepoPersonalPreferences](https://github.com/themorgan/RepoPersonalPreferences)
(the private repo the list itself lives in — the blocker the bullet above
named) answered the open redundancy question first, honestly rather than
by habit: does `full-practice-audit` (built 2026-09-03, after the bullet
above was written) already cover this need?

**No — the two ask different questions.** `full-practice-audit` asks,
practice by practice, a closed question against one document's own text:
"is this specific Rule satisfied?" RPP's list asks something no
per-practice sweep can answer no matter how many times it runs: does the
repo's *own writing*, taken as a set, still hold together? A contradiction
between two documents, a stale cross-reference, the same rule restated in
three places, a heading that drifted to the wrong capitalization scheme —
none of these is a violation of any single practice's Rule; each is a
property of the documents together. Confirmed by reading RPP's own
`deep-check` entry (`process/personal/README.md#deep-check`) against
`full-practice-audit.md` side by side rather than assumed from the names.

**Not redundant, so it was built**, following the exact pattern this
document's own "generalized finding" argues for doing consistently:
[practices/very-deep-check.md](../practices/very-deep-check.md) plus
[tools/very_deep_check.py](../tools/very_deep_check.py) — an on-demand
practice file and an enumeration-only engine, the same shape as
`routing-audit`/`full-practice-audit`, never wired into a commit, push, or
merge gate.

**The enumeration turned up something the v28 amendment's own author could
not have known.** The private-set migration that populated RPP's two
successor repos (v27, "Phase 3 closed") landed *earlier the same day*
(2026-09-01) as v28's "not yet inventoried here" line — and that migration
had already carried RPP's exact list into
[`precedent-team-maintainers`](https://github.com/themorgan/precedent-team-maintainers)
as its own `deep-check` practice, generalized (RPP's vendored-`process/`-tree
language dropped, since Precedent's private sets aren't vendored the way
RPP's own tree was) but otherwise the same enumeration now written here.
So the list was never actually missing during phases 5–6 — it just was
never recognized as fulfilling this commitment, since nobody cross-checked
the same day's two changes against each other, and it existed only as prose
in one private team practice with no companion engine and no reach outside
that one team's own set. `practices/very-deep-check.md` is the universal
version: reachable by any repo running Precedent, not only Morgan and
Alex's. Whether `precedent-team-maintainers`'s own `deep-check` should now
`overrides:` this one, or stand as a separate team-level restatement of the
same rule, is that team's own call to make — raised, not decided, here;
not actioned in this pass since it needs that set's own approver sign-off
([`precedent-team-maintainers`](https://github.com/themorgan/precedent-team-maintainers)'s
`approvers.json`), not something to decide from BestPractice.

`TODO.md` item 17 (the current position — item numbers shift as items are
inserted and closed, so the item-14 reference two paragraphs above is this
document's own now-stale cross-reference, left as an example rather than
fixed, since fixing it is exactly what a `very-deep-check` run would catch
and this document is not the deliverable that run was for) is closed
accordingly.

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
