---
title:         Very Deep Check: A Dedup Ledger for Repeat Findings
kind:          proposal
status:        executed
opened:        2026-09-20
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       Proposes, then records the landing of, the CONVERGENT DRIFT dedup ledger -- a per-set very-deep-check-decisions.json so a finding a person has already judged stops reprinting on every run -- from its handoff out of precedent-individual through the implementation that shipped it here.
---

# Very Deep Check: A Dedup Ledger for Repeat Findings

**Executed.** This proposal was written in `precedent-individual` (Morgan's
private individual source) by a session with no push access to this
repository, then handed off. A later session rooted here read it, built
sections 1-5 exactly as specified below, and landed the result in
[PR #483](https://github.com/alex137/BestPractice/pull/483) against
`precedent-beta-v01`. This document was then moved here from
`precedent-individual` — a project-wide engine proposal belongs in the repo
whose engine it changes, not in a private per-person source that cannot host
it for anyone else — and deleted there in the same change. "What shipped"
below records the implementation and the one place it departed from this
plan; everything from "## Situation" onward is the original handoff,
unchanged, kept for why the design is shaped the way it is.

## What shipped

- **Schema** — `very-deep-check-decisions.json` (section 1 below), unchanged
  from the proposal. The file already created in `precedent-individual` needed
  no rework.
- **Read side** — `tools/very_deep_check.py`'s `_convergent_drift()` gained a
  `sources=` parameter and now reads each converged set's ledger: a `DECIDED`
  line when every involved set agrees and no `revisit` date has passed, the
  ordinary `FINDING` annotated with partial or disagreeing verdicts otherwise,
  and `ORPHANED LEDGER ENTRY` for a decision naming a file no longer present.
  `sources=None` (every call site that predates this change) is unaffected —
  additive, as section 2 required.
- **Tests** — `tools/verify_harness.py`'s `check_very_deep_check_convergent_drift`
  gained the five stated cases from section 5 below, plus a sixth pinning
  that omitting `sources` ignores any ledger files on disk entirely.
- **`very-deep-check.md`** — the Pass 1 "sets, against each other" bullet, a
  dated Story entry, and an Install note, per section 4.
- **One departure, CI-caught, not proposed**: the first push linked this
  document by its `precedent-individual` URL from inside
  `practices/very-deep-check.md`. `check_practices_link_only_reachable_repos`
  failed the build — practice files ship verbatim into every consuming repo,
  so a link to a private repository is a 404 and a disclosure for every
  reader who isn't Morgan, exactly the mistake that check's own docstring
  already records this same file making once before, 2026-09-06, about the
  same two repos. Fixed by naming the document instead of linking it,
  everywhere `practices/very-deep-check.md` mentions it; this document itself
  is under `spec/`, which the check exempts, so it links freely.

Not built, per "Not proposed here" below and unchanged by the implementation:
the ledger shape is not extended to any other very-deep-check section, and
nothing populates an entry automatically.

---

**Output for a later BestPractice-rooted session.** Nothing here has been
applied upstream: this session had `themorgan/precedent-individual` in
scope only, and attaching `alex137/BestPractice` with push access was
refused outright by the harness's own permission classifier — a
repo-owner permissions issue, not something to route around. This is a
proposal, not a decision — strength: proposed. Morgan asked for it to be
written up in full, with context, so a session with no memory of this
conversation can act on it.

## Situation

On 2026-09-20, a background notification — from a different, already-ended
session, self-described as software-generated and explicitly flagged as
not user input — reported four supposed drift findings against
`precedent-individual`. Verifying each one directly (rather than trusting
the relay) found: two were real and got fixed (a stale vendored engine,
refreshed; a stale watermark, advanced to the actually-current commit); one
(a claimed mismatch between this repo's generated views and what
`precedent_bootstrap_source.py` would write) was checked against the wrong
tool and was actually clean (`build_views.py --check` — the tool that
governs those files' freshness — passed byte-identical); and one was
explicitly informational and outside this repo's own ability to verify:

> a line in `.claude/settings.json` and 23 lines in `AGENTS.md` are
> identical across all 3 `precedent-shared-*` repos and absent from what
> the generator writes — either something the template should pick up, or
> an older build all three share.

**This fourth item is cited here only as the motivating example, not as a
confirmed finding** — this session has no access to the three
`precedent-shared-*` repos to check it independently, and the relay that
reported it got enough else wrong (a fabricated file path, a nonexistent
file, a watermark SHA that was itself three commits stale) that nothing in
it should be taken on faith.

What the fourth item's *shape* does establish: it is exactly what
`very-deep-check.md`'s Pass 1 bullet "The sets, against each other" already
exists to catch — implemented as the `CONVERGENT DRIFT` section of
`tools/very_deep_check.py` (`_convergent_drift()`). That section intersects
the per-file differences already computed against the template and reports
any file that **two or more independently-drifted sets of the same level**
changed the same way, on the reasoning that one set's difference is a
person's choice, but two sets converging on it is a habit the template is
missing. It explicitly does not say which side is right — the shared
change might be something the template should adopt, or something the sets
share that the generator has since moved past.

## The gap

Discussing this with Morgan, the question was whether a check like this
could be added with minimal noise. Investigating found the mechanism
already exists — nothing to add there. What's actually missing: **`_convergent_drift()`
has no memory across runs.** Every file that still differs the same way in
two or more sets prints as a fresh `FINDING` on *every single run*, forever
— including a file a person has already looked at and explicitly judged to
be intentional per-repo customization, never going to generalize. That is
the actual source of noise in a check whose own practice file describes it
as "occasional... because the judging is expensive" — re-litigating the
same judged case on every run is exactly the expense it should not have to
keep paying.

Morgan asked for a dedup ledger to fix this, and — asked whether the fix
should just be a private implementation detail inside `_convergent_drift()`
— said it should be broader: a convention any repo can hold its own record
in, not state `very_deep_check.py` keeps privately to itself.

## What this session could do, and what it couldn't

`tools/very_deep_check.py` and the `very-deep-check` practice are scoped
`engine-dev` in their own frontmatter and live entirely in
`alex137/BestPractice`. Neither is vendored into `precedent-individual` —
confirmed by checking `tools/ENGINE_MANIFEST.json`'s tracked file list,
which does not include `very_deep_check.py` — so there is no local copy of
the scanning code to edit here, and this session cannot push to
`alex137/BestPractice` to edit the real one.

What *is* actionable from `precedent-individual`: the ledger's data half.
A dedup ledger only works if each repo whose findings it suppresses can
hold its own record — the decision belongs to the repo the finding is
about, the same reason `beta-branch-watermark.json` (a record of what
Morgan has already been told about a different upstream) lives in this
repo rather than in BestPractice. So this session created
`very-deep-check-decisions.json` at this repo's root: empty, schema-documented
in its own `_comment` block, ready for BestPractice's engine to read once
the code below exists. A repo with no such file, or an empty one, behaves
exactly as today — this is additive, not a breaking change to the check.

## Proposed design (for BestPractice)

### 1. Per-repo ledger file: `very-deep-check-decisions.json`

Schema, matching the file already created in `precedent-individual` (see
that file's own `_comment` for the identical text):

```json
{
  "entries": [
    {
      "section": "CONVERGENT DRIFT",
      "key": ".claude/settings.json",
      "verdict": "intentional-customization",
      "note": "why, in the decider's own words",
      "decided_by": "Morgan",
      "decided": "2026-09-20",
      "revisit": "2027-03-20"
    }
  ]
}
```

- `section` — which very-deep-check section produced the finding
  (`CONVERGENT DRIFT` today; the same shape would fit other sections later,
  see "Not proposed here" below).
- `key` — the section's own stable identifier for the finding. For
  `CONVERGENT DRIFT` this is the file path that converged — never a
  content hash or line number, both of which change on the file's next
  ordinary edit and would silently stop matching, turning a suppressed
  finding back into a surprise `FINDING` for a reason nobody intended.
- `verdict` — one of four fixed values (see below), not open text — kept
  small and closed so the tool can act on it rather than merely print it.
- `note`, `decided_by`, `decided` — same shape as `identity.json`'s
  `grandfathered_commit_shas` list, which this design is modeled on
  directly: every entry needs a person's explicit, dated, quoted judgment.
- `revisit` — optional. A date after which the tool re-surfaces the
  finding for reconfirmation instead of suppressing it forever, mirroring
  Pass 3's `GOTCHA CURRENCY` re-verification (`very-deep-check.md`): a
  decision that was right in September can be stale by March, and nothing
  should trust it blindly past the date the decider themselves picked.

### 2. Read-side change: `_convergent_drift()`

Before printing `FINDING` for a converged file, check the ledger of every
set involved in that convergence for an entry keyed
`("CONVERGENT DRIFT", <file path>)`:

- **All involved sets that have a ledger agree on a verdict** → print a
  shorter line instead of `FINDING`: `DECIDED (<verdict>, by <decided_by>
  <date>): <file>`. Visible, not silent — this system's own principle from
  the "quiet is not the same as useless" passage in `very-deep-check.md`
  applies here exactly as it does to a guard that never fires.
- **Sets disagree, or only some have recorded a verdict** → print the
  ordinary `FINDING`, annotated with which sets have already decided and
  what they said. A disagreement between sets about the same convergence
  is itself worth a person's attention, not something to average away or
  suppress on a majority.
- **`revisit` date has passed** → treat the entry as expired, print the
  ordinary `FINDING` again.
- **A ledger entry names a file no longer present, or a set no longer in
  force** → report it as `ORPHANED LEDGER ENTRY` rather than silently
  ignoring it, matching the existing `ORPHANS` section's own philosophy of
  naming a stale record rather than dropping it quietly.

### 3. Where the verdict comes from

Never written automatically. A person — or a session acting on their
explicit instruction — adds an entry after reading a `FINDING` and
deciding what it means. Four verdicts, deliberately closed rather than
open text:

- `intentional-customization` — this repo's own choice; will not
  generalize; the template should not adopt it.
- `template-candidate` — the convergence is real evidence the generator is
  missing something; someone should file a fix in the generator or
  template.
- `stale-shared-build` — the sets share an older build the generator has
  since moved past; the sets are wrong, not the template.
- `tracked-elsewhere` — already has a TODO or decision record; the ledger
  just stops the tool from re-discovering it as new every run.

### 4. `very-deep-check.md` changes

- Extend the "The sets, against each other" bullet in Pass 1 with a
  paragraph describing the ledger, its four verdicts, and the `revisit`
  mechanism, citing this proposal.
- Add a dated `Story` entry (this file's own established citation
  convention — every past revision quotes Morgan verbatim) recording this
  request.
- Add an `Install` note describing `_convergent_drift()`'s dedup behavior
  and stating explicitly that a repo with no ledger file is unaffected —
  worth saying outright given how carefully this file already documents
  backward-compatibility elsewhere (e.g. the `hook_files` "vendored before
  hook scripts were tracked" case in `precedent_vendor_engine.py`).

### 5. Test coverage

- Two sets converge on a file, no ledger present → `FINDING` (today's
  behavior; must not regress).
- Same fixture, plus a ledger entry with a matching verdict from every
  converged set → `DECIDED` line, not `FINDING`.
- Same, but only one of the converged sets has decided → `FINDING`,
  annotated with the partial verdict.
- Same, but the entry's `revisit` date is in the past → `FINDING` (decision
  treated as expired).
- A ledger entry naming a file no longer present in that set →
  `ORPHANED LEDGER ENTRY`.

## Not proposed here (kept out of scope deliberately)

- **Extending the same ledger shape to other very-deep-check sections**
  (`BOOTSTRAP DRIFT`, `ORPHANS`, the coverage report in Pass 2's question
  15, etc.). The noise problem was raised specifically about `CONVERGENT
  DRIFT`; the same shape would likely help elsewhere, but widening it now
  before this version is even built and proven is the exact scope creep
  this system's own practices warn against. Worth a `TODO.md` line in
  BestPractice once this lands, not part of this ask.
- **Auto-populating the ledger from a heuristic** ("looks like a personal
  customization"). The entire point is that a person judges it once;
  automating the judgment defeats the reason the ledger exists.

## Handoff

A session rooted in `alex137/BestPractice`, with push access there, should:
read this file in full, implement sections 1–5 above (the schema in
section 1 must match `very-deep-check-decisions.json` in
`themorgan/precedent-individual` exactly, so that repo's file needs no
rework once the read side exists), add the tests in section 5, extend
`very-deep-check.md` per section 4 with the same dated-quote convention
every prior revision in that file uses, and open a pull request against
`precedent-beta-v01`.

**Done** — see "What shipped" above.
