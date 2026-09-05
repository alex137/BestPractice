<!-- Last updated: 2026-09-01 (Buenos Aires) by a pre-phase-5 slug-citation session, to version 3 -->

# The Practice File Format

This is the format [`tools/split_practices.py`](../tools/split_practices.py) converts BestPractice's
[`PRACTICES.md`](../PRACTICES.md) into, and the format any future practice (universal, team, or
individual) is authored in. It implements
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s "The Practice File"
section. Read that first; this document only covers where this
implementation had to make a call the plan's own illustrative example didn't
settle, and says so plainly rather than presenting those calls as if they
were already decided.

## The Shape

One file per practice, at `practices/<slug>.md`:

```
---
slug:        kebab-case-slug
title:       Human-readable title (no leading practice number)
tier:        on-demand          # resident | on-demand
severity:    default            # blocking | default | advisory
applies_to:  ["**"]             # path globs
occasion:    "prose trigger"
gates:       []                  # named moments -- see below
index_clause: "the one line the occasion index shows"   # see below
checked_by:  tools/x.py or null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null                # see "What's deferred" below
approved_by: "BestPractice (pre-fork)"
source_practice_number: N        # see "Beyond the plan's example" below
---

## Rule
...

## Detail
...                               # added at phase 3 -- see below

## Why
...

## Story
...                               # empty in every phase-1 file -- see below

## Install
...                               # not in the plan's own example -- see below
```

[`tools/precedent_show.py`](../tools/precedent_show.py) is the one code path that reads these files; per
the plan's own "Loading a Practice Means Loading Its Rule, Not Its File",
nothing else should open a `practices/*.md` file directly once this exists.

## Two Places This Implementation Goes Beyond The Plan's Illustrative Example

The plan's own frontmatter example and three-section body (Rule/Why/Story)
is illustrative, not a complete spec — building the actual converter against
BestPractice's real 52 practices turned up two gaps a real implementation
has to resolve one way or another. Both are phase-1 judgment calls, made
and recorded here rather than silently decided; both are reversible.

**1. A fourth section, `## Install`.** *(A fifth, `## Detail`, followed at
phase 3 — see [The Rule/Detail Split](#the-ruledetail-split-phase-3).)* BestPractice's own catalogue is
Rule + Why + Install, in every one of its 52 practices — "Install" is how a
dependent repo actually installs the practice: template paths, tool names,
wiring instructions. The plan's example has nowhere for that text to go.
Dropping it would violate the plan's own no-invented-content rule for the
converter (Migration, "The Converter": "the converter may move and drop
text, never invent it" — dropping is allowed, but dropping the single most
actionable part of every practice is not a reasonable reading of that
license) and would make "the catalogue regenerates byte-identically"
(Sequence, phase 1's done-when) unachievable, since the original file has
nothing else in it. So: `## Install` is a fourth section here, on-demand
like Why and Story. Whether it belongs in the *long-run* format, folded into
`checked_by`/a future installer command, or kept as prose, is a real
open question for phase 2 or 3 — flagging it here rather than presenting it
as settled.

**2. `## Story` is present but empty, in all 52 files, for now.** *(Superseded
by the phase-1.5 editorial pass — see [The Editorial Re-Split](#the-editorial-re-split-phase-15)
below. 19 of the 52 now carry a real Story. The reasoning recorded here is kept
because it explains why phase 1 stopped where it did.)* The
plan's Rule/Why/Story split asks for a second split beyond the mechanical
one: separating the *incident* (Story) from the *reasoning* (Why) within
what BestPractice calls "Why" — and the plan itself describes that step as
"LLM-assisted and human-reviewed, once per practice" (Migration, "The
Converter"). Doing that with real care, per practice, for 52 practices,
unreviewed, in one pass risked mischaracterizing exactly the content this
plan exists to preserve faithfully — and the plan's own no-invention rule
is stricter than "roughly right." So this conversion does the mechanical
half only: BestPractice's "Why" text, in full, lands in `## Why` here, and
`## Story` is a real section header with no body — a declared gap, not a
silent one. The token-budget upside of the Rule/Why/Story split does not
depend on Story specifically being populated (see "Loading a Practice Means
Loading Its Rule, Not Its File" in the plan: the resident/on-demand
boundary is Rule vs. everything else) — only the archival and
"question-without-pulling-in-history" benefits of splitting Why from Story
specifically are deferred, not lost. Splitting the 52 Story sections out by
hand, with review, is real follow-on work; it is not blocking for phase 1's
own done-when condition ("Practices are files; the catalogue regenerates
byte-identically; harness passes").

## The Editorial Re-Split (Phase 1.5)

Phase 1's converter routed each paragraph by the bold label that opened it.
That is lossless but not editorial, and it left the plan's headline claim
undelivered:

> "BestPractice's median practice is 38 lines; the instruction inside it is
> three or four. Splitting removes roughly nine tenths of the resident text
> without deleting a word."

After phase 1, `## Rule` was **44%** of the catalogue, not a tenth. Sixteen
practices had Rules over 150 words, the longest ran to 1,340, and the six
practices whose source opens on bare prose (47–52) had their *entire* body
land in `## Rule`, because the label walk never saw a `**Why.**` to leave on.
`## Story` was empty in all 52.

[`tools/resplit_sections.py`](../tools/resplit_sections.py) performs the
second, editorial half — the step the plan describes as "LLM-assisted and
human-reviewed, once per practice". The editorial judgment lives in
[`tools/practice_metadata.json`](../tools/practice_metadata.json)'s sibling,
`tools/section_split.json`, as **references to source paragraphs** rather than
as rewritten text: the tool moves text by reference, so retyping a sentence
slightly differently is not something the mechanism can do, and a reviewer can
read the decisions on their own, apart from their effect. Every one of the 52
is listed explicitly, and every source paragraph must be placed — a paragraph
cannot be dropped by omission.

### What it delivered, and what it did not

| | after phase 1 | after phase 1.5 |
|---|---|---|
| `## Rule` share of the catalogue | 44% | **40%** |
| Practices with a non-empty `## Story` | 0 | **19** |
| Words in `## Story` (never loaded) | 0 | **2,381** |
| Words in `## Why` (loaded only to question a practice) | 2,437 | **3,752** |

**The plan's "nine tenths" estimate does not hold for this catalogue, and
that is a finding rather than a failure of the pass.** BestPractice's
practices carry far more genuinely *normative* text than the estimate
assumed — numbered policy rules, worked decision procedures, sub-rules with
their own tests. Loading a practice's Rule costs roughly 40% of its file, not
10%. That is still a real saving, and Story and Why now hold 6,100 words that
never enter a working session's context; it is not the saving the plan
advertised.

**The underlying reason is worth carrying into phase 3: the four-section
format has no home for detailed normative elaboration.** A numbered list of
policy rules is not reasoning (`Why`), not an incident (`Story`), and not
wiring (`Install`) — so it stays in `Rule` and keeps `Rule` long. Twenty
practices still have Rules over 150 words for exactly this reason. Either the
format grows a fifth section, or `Rule` is understood as "everything
normative" and the resident budget does the trimming instead. Not decided
here.

*(Decided since: the format grew the fifth section. See
[The Rule/Detail Split](#the-ruledetail-split-phase-3) below.)*

### What the pass may and may not do

Content preservation is enforced, not asserted. See
[`tools/verify_harness.py`](../tools/verify_harness.py):

- **content preserved sentence-for-sentence** — every sentence of every
  practice, against `PRACTICES.md`, in both directions.
- **section content keeps its source order** — text may be re-homed, not
  scrambled.
- **markdown list structure preserved** — the sentence checks normalize
  whitespace, so they cannot see a flattened list; this can.

Byte-identical regeneration was **retired** in this pass, because it cannot
survive a re-split by construction: moving a paragraph from Rule to Why moves
where the rebuild emits the `**Why.**` label, so the diff is non-empty however
faithful the move was. Its content claim is now made more strongly by the
sentence check, and its ordering claim by the source-order check. A check that
fails on correct work gets suppressed, and is then absent when something is
actually wrong. `tools/split_practices.py build --diff` still runs; its diff is
now expected output showing the re-split, not a defect report.

## The Rule/Detail Split (Phase 3)

`## Detail` is the fifth body section, added by
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) v20 and applied here.
It holds **normative operational specifics** — numbered policy rules, worked
procedures, sub-rules with their own tests: text that is binding but is not
needed to decide *whether* the practice applies. Same machinery as the
phase-1.5 pass ([tools/resplit_sections.py](../tools/resplit_sections.py)
over [tools/section_split.json](../tools/section_split.json)), so the
decisions are reviewable as data and the text moves by reference rather than
being retyped.

Two constraints from the plan's phase-3 row governed every decision:

- **`## Rule` must stay loadable on its own.** A session that reads only the
  Rule must know what to *do*, not merely that something applies. This is the
  binding constraint, and it is what stopped three practices from being split
  at all.
- **`## Detail` comes from the same command.** `precedent show SLUG --detail`,
  never a second tool — a second extractor is one more thing to drift from
  [tools/precedent_show.py](../tools/precedent_show.py).

### What it delivered

| | after phase 1 | after phase 1.5 | after phase 3 |
|---|---|---|---|
| `## Rule` share of the catalogue | 44% | 40% | **28%** |
| Practices with `## Rule` over 150 words | 16 | 20 | **7** |
| Resident block, generated | — | ≈621 tokens | **≈312 tokens** |
| Words in `## Detail` | — | — | **2,778** |

Sixteen of the fifty-two practices carry a Detail. The resident block — the
text every session pays for, whatever it is doing — **halved**, which is the
closest this catalogue has come to the plan's "nine tenths" claim and still
short of it.

*(Both figures in this table are scoped to BestPractice's original 52
practices — `tools/catalogue_stats.py`'s `phase3_snapshot_stats()` — so they
stay a stable record of what phase 3 delivered rather than drifting every
time a later practice is added or an inherited one is deliberately rewritten
(`CHANGES_TO_TELL_ALEX.md`). The "over 150 words" figure moved from 8 to 7
on 2026-09-01, when `layered-practice-packs`' Rule was shortened as part of
that rewrite. The "carries a Detail" figure moved from 15 to 16, and "Words
in `## Detail`" from 2,253 to 2,778, on 2026-09-05, when `session-bootstrap`
gained a real Detail — see `CHANGES_TO_TELL_ALEX.md`. Only the two figures
`tools/catalogue_stats.py` prints an anchor for — the Rule-share-derived
counts, not the raw word totals — are mechanically checked against this
table; the word-count cells are updated by hand alongside them.)*

*(These are the figures after the review pass described in
[What a Reader Caught That No Check Did](#what-a-reader-caught-that-no-check-did)
below, which reverted two splits. The first pass reported 27%, 7, and
seventeen.)*

### The five practices that could not be split, and why that is a finding

The mechanism moves text; it cannot write text, because the no-invented-content
rule forbids it. So a practice can only be split where the source already
has a seam. Five do not:

| slug | Rule words | why it is irreducible |
|---|---|---|
| `permutation-frontier-column` | 358 | The framing paragraph ends *"Three rules:"* and the three rules are one markdown list, which cannot be sliced without flattening it. Rule alone would say a table is being built and stop. |
| `verify-decomposition` | 329 | Names two failure modes. With the fixes for the first in Detail, the Rule diagnosed it — *"the tell is a headline number that survived several passes"* — and then prescribed nothing. Reverted by the review pass below. |
| `mistakes-become-rules` | 228 | One 171-word paragraph in which every sentence is an instruction — root-cause it, encode at the strongest rung, discuss the judgment call — plus a proportionality guard that gates *whether the rule fires at all*. Moving the guard to Detail would leave a Rule that mints a practice for every slip, which is the failure the plan opens by diagnosing. |
| `scripts-assert-properties` | 227 | Its closing paragraph is a **scope gate** — which scripts to instrument, and that scripts owning their numbers end to end need nothing. Detail is defined as what is not needed to decide whether a practice applies, and a scope gate is exactly that. Reverted by the review pass below. |
| `build-buy-decompose` | 224 | The second of its two moves defines the ownership/capability distinction that the closing instruction depends on; moving either half leaves the other dangling. Only the embedded origin anecdote could be re-homed. |

**This is a property of the source text, not of the pass.** BestPractice's
practices were written as continuous prose, and a seam only exists where the
author happened to leave one. Splitting the remaining seven would mean
writing a new lead-in sentence — which is exactly the invention the converter
is forbidden to do, and which would break the sentence-for-sentence check
that makes the whole conversion trustworthy. Doing it deliberately, as an
authored edit reviewed against the source, is real work; it is not this
pass's work, and pretending the mechanism could have done it would
misdescribe why the number stopped where it did.

### What a Reader Caught That No Check Did

The seventeen splits were made in one pass, and then read back — each `## Rule`
on its own, as `precedent show SLUG` returns it, with nothing else loaded.
**Three were wrong.** Every check in the harness passed on all three, and the
content-preservation net was never in question: nothing was lost, invented or
reordered in any of them. What was wrong was the judgment the net cannot see.

| practice | what the Rule said on its own | verdict |
|---|---|---|
| `verify-decomposition` | Named two failure modes, gave the tell for both, and the prescribed fix for only one. A session reading it would diagnose the first and be told nothing to do. | Reverted |
| `scripts-assert-properties` | Lost its scope gate to Detail, so a session reading only the Rule would instrument every script rather than the ones that re-derive another owner's quantity. | Reverted |
| `layered-practice-packs` | Its decision rule routes a rule to *"the pack"* — and the sentence defining what a practice pack **is** had moved to Detail. The Rule used a term it never defined. | Definition restored to Rule; only the routing aside stays in Detail |

**The line that came out of it, and that the remaining splits were re-checked
against:** `## Detail` may hold sub-rules and elaboration; it may **not** hold
anything needed to decide *whether, or how widely, the practice applies*. That
is the plan's own definition of Detail read strictly — *"not needed to decide
whether the practice applies"* — and it is what separates
`scripts-assert-properties`' scope gate (belongs in Rule) from
`reply-links-files`' rendered-view sub-rule (belongs in Detail).

**One of the three had a mechanical signature and now has a check.** A Rule
ending on a colon has had its payload moved out and announces a list it does
not contain; `check_rule_is_self_contained` in
[tools/verify_harness.py](../tools/verify_harness.py) fails on it, and was
verified by re-applying the split that would have dangled. The other two —
a scope gate that moved, a term defined only in Detail — are judgments about
meaning, and **there is no check for them**. They needed a reader. That is
worth saying plainly rather than implying the harness now covers this.

### One tension worth recording rather than smoothing over

`verify-postcondition` is the catalogue's most-missed resident practice
([What Phase 2 Measured](../PRACTICE_ENGINE_PLAN.md#what-phase-2-measured):
judged applicable twice, named by the full-catalogue control **zero** times),
and this pass moved its two most concrete parts — the pipeline-exit-status
trap and the explicit-target trap — out of the resident Rule and into Detail.
The split is correct by the plan's rule (they are elaboration; the Rule stands
alone without them) and it is the single largest contributor to halving the
resident block. It may also make that practice's misses worse.

Phase 2's own measurement is the reason not to guess either way: **residency
did not produce compliance for this practice at any catalogue size**, so
keeping 117 more words resident had no measured benefit to protect. The
answer the plan points at is phase 4 — `verify-postcondition` carries
`checked_by: null` and is on phase 4's starting queue. Recorded here so that
whoever runs the routing eval after phase 4 knows this changed underneath it.

## `gates` (Phase 4)

Not in the plan's frontmatter example, and load-bearing for the channel the
plan *does* name. **Gate-triggered** is the fourth loading channel —
*"Runbook steps cite slugs; reaching the step loads them. A merge loads
exactly the merge practices, at the moment of merging."* — and nothing carried
the association between a practice and a moment until this field.

```
gates:       ["merge"]
```

**Why a moment cannot be a glob, which is the whole argument for the field.**
Phase 4's routing pass gave a narrower `applies_to` to every on-demand
practice with a genuine path locus and recorded the reason for every one that
kept `**` ([tools/routing_scope.json](../tools/routing_scope.json)). Twenty-six
kept it, and the most common reason was the same: **the practice fires at a
moment, not in a place.** `merge-runbook` fires when merging.
`mistakes-become-rules` fires when a review turns up a defect. No glob reaches
either, however well written, and the plan forbids widening the occasion index
to compensate.

Four rules govern the field, all enforced by
[tools/verify_harness.py](../tools/verify_harness.py)'s `check_gate_channel`:

- **The vocabulary is closed.** Gate names are declared once, in
  `tools/routing_scope.json`, with the moment each one is. A practice naming
  an unknown gate fails the harness — a typo in a gate name would otherwise
  register a practice to a moment nobody reaches.
- **No gate may be empty.** A gate with no practices prints nothing and exits
  0, which is indistinguishable from a gate that legitimately had nothing to
  say. [tools/precedent_gate.py](../tools/precedent_gate.py) refuses one by
  name, and the harness refuses one in the vocabulary.
- **Every gate resolves.** The harness runs the command for each gate as a
  subprocess and requires every registered slug in the output.
- **At least one gate is wired to something automatic.** The `push` gate is
  invoked by [templates/hooks/pre-push](../templates/hooks/pre-push), so it
  fires whether or not anyone remembers it. The harness fails if that wiring
  is removed.

**What this channel does not settle**, stated here rather than left to be
discovered: reach is deterministic *given that the gate is invoked*. Three of
the four gates are invoked by a runbook step or the standing instruction,
which is a session remembering to — the same weakness the occasion index has.
Only `push` is wired. Whether a practice reaches a session through `merge`,
`review` or `reply` is therefore a wiring question, and phase 6's consumer-repo
integration is where the remaining three get hooks.

**The routing eval cannot see any of this.** It replays twenty commits against
the resident block, the occasion index and the path channel; a gate fires at a
moment a commit does not record. No recall figure is attributable to this
channel, and none is claimed.

## `index_clause`

Not in the plan's frontmatter example, and load-bearing anyway: the occasion
index is the **only** route to 34 of the 46 on-demand practices, and a
session decides whether to open a practice on the strength of one line.

Phase 2 derived that line — the Rule's first sentence, cut at 90 characters.
**86% of the 46 entries came out truncated mid-thought**, and one ended on a
dangling colon:

```
name-both-sides-of-ledger — When a model charges one party for what another receives — work for kinetic energy, spe...
docs-track-models — Extending practice 19 from *tables* to **every** figure a script computes:
```

The plan's own worked example is not a derived first sentence; it is a
written clause — *"references are links; ≈ not ~"*. So the clause is
authored, one per on-demand practice, and
[`tools/verify_harness.py`](../tools/verify_harness.py) requires it: present,
under 80 characters, finishing its thought, and reading as a table cell
rather than a sentence. Derivation stays as a fallback so a newly added
practice renders something before its clause is written.

This is metadata for a generated view, not practice text — the
no-invented-content rule governs Rule/Why/Story/Install, which this never
touches.

**Two `occasion` strings were rewritten in the same pass**, for a defect
[spec/LOADER.md](LOADER.md) already names in another practice: an occasion
that describes the *error state* rather than a work moment a session can
recognize is unroutable, because recognizing it means already having avoided
the mistake.

| slug | was | now |
|---|---|---|
| `verify-decomposition` | trusting a model's total without checking its parts | reporting a computed total or a negative feasibility result |
| `search-by-purpose` | concluding that no prior work exists on a question | starting work the repository may already cover |

## `source_practice_number`

Not in the plan's frontmatter example, and necessary anyway: the Migration
section's verification harness explicitly requires "citation integrity —
every existing citation resolves, including the 169 by-number `practice N`
references." Slugs are the practice's permanent identity going forward, but
the *existing* catalogue and every existing citation into it are numeric.
This field is the join key that lets [`tools/verify_harness.py`](../tools/verify_harness.py)'s citation
check, and eventually a real migration tool, resolve `practice 20` to
`mistakes-become-rules`. It is a phase-1/migration-bridging field, not part
of the practice's own identity — a promoted team or individual practice
minted fresh, with no BestPractice-numbered ancestor, simply won't have one.

It stays mandatory for the 52 practices converted from BestPractice's
numbered catalogue and optional for everything minted after the fork — that
was already the design intent above, stated here as the explicit, settled
policy since the question is a natural one to ask now that slugs are the
citation form everywhere (next section). A `BP23`-style prefixed variant
(folding the provenance into the number itself) was considered and rejected:
the frontmatter key already carries that provenance once, and a bare integer
is what every actual consumer of the field (`verify_harness.py`'s
citation-integrity check, `split_practices.py`'s sort key) wants — a string
tag would just be a second way to say what the key name already says.

## Citing Other Practices

**Slugs are practices' official identity and their official citation form,
always as a markdown link: `[some-slug](some-slug.md)`.** This was already
true in the plan (`slug: … # permanent identity; cited by name`), but the 52
phase-1 files' own prose had not caught up: they still cited each other the
old way, as bare `practice N` / `practices N and M` text, carried forward
verbatim by the phase-1 converter's own "move, never invent" rule. A
catalogue built to let practices be reordered, split, and retired
independently (this fork's whole reason for moving off fixed numbers — see
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md), "Practices cited by
position … making insertion a cross-repo sweep") cannot leave its own
cross-references pointing at position. A pre-phase-5 session (2026-09-01)
swept every `practices/*.md` file and replaced each cross-reference with a
slug link, resolved against the practice's actual content rather than just
its printed number — see
[CHANGES_TO_TELL_ALEX.md](../CHANGES_TO_TELL_ALEX.md) for the full list,
including four pre-existing miscitations the sweep found and fixed.
[`tools/verify_harness.py`](../tools/verify_harness.py) holds this going
forward with two checks: `check_no_bare_numeric_citations` fails if a bare
`practice N` reappears in body prose, and `check_slug_link_integrity` fails
if a `[slug](slug.md)` link points at a slug that does not exist.

Converting a citation to a link is a real, disclosed content edit relative to
BestPractice's frozen original — it adds words (the slug name) the fidelity
checks below did not count at that frequency — so every affected slug is
registered in `verify_harness.py`'s `AMENDED_POST_CONVERSION` and logged in
`CHANGES_TO_TELL_ALEX.md`, per that mechanism's own rule that an exemption
must be both declared and actually findable there.

## What's Deliberately Left For Later

- **`added` is `null` for all 52.** Backfilling it means finding, per
  practice, the earliest commit that introduced that practice's text in
  BestPractice's history — the shallow clone this conversion worked from
  (`--depth 1`, to avoid a slow full-history fetch through the session's git
  proxy) has no history to blame against. A full clone and a `git log -S`
  pass per practice would fill this in; not done here because it doesn't
  block phase 1's done-when condition and a shallow fork is the right
  default for day one regardless (Risks: "keep universal practice text as
  close to upstream's wording as possible" says nothing about needing full
  history on disk).
- **`tier` was `on-demand` for all 52 at phase 1; phase 2 curated 6 to
  `resident`** once the budget mechanism existed to enforce the choice —
  see [spec/LOADER.md](LOADER.md) for which six and why. `severity` is
  still `default` for all 52 at phase 2. `severity`'s only real job
  (Severity, Not Ranking) is resolving conflicts between sources at
  different precedence, which does not arise until team and individual
  sources exist (phase 3) — so `default` for everything is not a
  placeholder guess, it is the correct value until there is a second source
  to conflict with.
- **`checked_by` and narrower `applies_to` are set only where mechanically
  unambiguous** from the original Install text (roughly a dozen of the 52 —
  see `tools/practice_metadata.json`). Every on-demand practice also gets an
  `occasion` string, which alone satisfies the plan's reachability
  requirement (every on-demand practice needs *at least one* of
  `checked_by` / narrow `applies_to` / `occasion`) — so reachability holds
  for all 52 without claiming enforcement accuracy this pass didn't do the
  work to earn.

## A Genuine Upstream Finding

Converting the catalogue mechanically (rather than reading and rewriting
each practice by hand) surfaced a real defect in BestPractice's own
`PRACTICES.md` at the commit this fork is based on (`88ecf7f`): practice
39's body is followed, in the source file, by a stray duplicate of part of
practice 34's body (a paragraph beginning "es a source's vocabulary within
a single session..." — the tail end of a sentence that belongs, whole, to
practice 34, pasted a second time immediately after practice 39's own
`Install.` paragraph, with no heading of its own). This reads as a bad
merge or copy-paste in BestPractice's own history, not authored content.
`tools/split_practices.py` drops it explicitly and by name
(`FIXUP_39_MARKER`), and [`tools/verify_harness.py`](../tools/verify_harness.py)'s byte-identical-
regeneration check treats exactly that removal — plus two whitespace-only
quirks, a stray blank line between practices 40 and 41 and the file's one
`**Install.**` label followed by a newline instead of a space — as the
three sole approved exceptions to an otherwise-exact diff against the
original.

**Where the first pass got this wrong, since it is the instructive part.**
The stray fragment is pasted *mid-paragraph*: it begins mid-word on the
line immediately after practice 39's own `**Install.**` paragraph ends,
with no blank line between them. The converter's first version dropped
from the preceding *blank* line instead, which deleted practice 39's whole
Install paragraph — its template path, its wiring, the propagation
instructions — along with the corruption. **Every check in the harness
passed.** The no-invented-content check is a subset test, so a deletion
satisfies it trivially; and the byte-identical exception had been
hand-written to the same wrong boundary, so it agreed with the converter
instead of catching it. Two checks were added in response: a `no lost
content` mirror (making the word-multiset comparison an equality rather
than a subset), and `corruption drop is a verbatim duplicate`, which
asserts that whatever the converter drops occurs verbatim elsewhere in the
file. The second is the one that actually catches it, because it tests a
property of the dropped *text* rather than re-deriving the boundary — a
check that recomputes the boundary cannot catch a converter that got the
boundary wrong. Worth reporting upstream at the next real check-in (phase 7 territory,
or sooner if Alex wants to hear about it before then); not fixed upstream
by this session, which only has read access to `alex137/bestpractice`.

## Tooling

- `tools/split_practices.py split` — `PRACTICES.md` → `practices/*.md`.
- `tools/split_practices.py build [--diff]` — the reverse, for the
  byte-identical-regeneration check.
- [`tools/verify_harness.py`](../tools/verify_harness.py) — runs every check from the plan's verification
  harness that is meaningful given what exists; the rest report as
  not-yet-applicable, not as passed.
- `tools/precedent_show.py SLUG... [--why|--story|--install]` — the one
  code path an agent (or a human) uses to load a practice; never read
  `practices/*.md` directly.
