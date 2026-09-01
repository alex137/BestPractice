<!-- Last updated: 2026-09-01 (Buenos Aires) by a pre-phase-5 slug-citation session, to version 2 -->

# The Practice File Format (Phase 1)

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

**1. A fourth section, `## Install`.** BestPractice's own catalogue is
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

**2. `## Story` is present but empty, in all 52 files, for now.** The
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

`source_practice_number` stays exactly as phase 1 defined it: **mandatory
for the 52 practices converted from BestPractice's numbered catalogue,
optional for everything minted after the fork** (a team or individual
practice with no BestPractice-numbered ancestor has nothing to record here).
This was already true the moment the field was designed as a
migration-bridging join key rather than part of a practice's identity; it is
recorded here as the explicit, settled answer rather than left implicit,
since the question of whether to make it mandatory going forward is a
natural one to ask once slugs are the citation form everywhere else.

A deliberately rejected variant, since it was raised while doing this sweep:
prefixing the number itself (`BP23` rather than a bare `23`) to mark its
BestPractice origin inline. Not done — the frontmatter key
(`source_practice_number`) already carries that provenance, a bare integer
is what every consumer of the field (`verify_harness.py`'s citation-integrity
check, a future migration tool doing `int()` comparisons) actually wants,
and a string tag would just be a second, redundant way to say "this came
from BestPractice" that the key name already says once.

## Citing Other Practices

**Slugs are practices' official identity and their official citation form,
always as a markdown link: `[some-slug](some-slug.md)`.** This was already
true in the plan (`slug: … # permanent identity; cited by name`) and in
practice — every one of the 52 phase-1 files already had its permanent slug
— but the 52 files' own prose had not caught up: they still cited each other
the old way, as bare `practice N` / `practices N and M` text, inherited
verbatim from BestPractice's numbered catalogue by the phase-1 converter's
own "move, never invent" rule. A repo about to let practices be reordered,
split, and retired independently (this fork's whole reason for moving off
fixed numbers — see [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md),
"Practices cited by position … making insertion a cross-repo sweep") cannot
leave its own cross-references pointing at position. A session before phase
5 (2026-09-01) swept every `practices/*.md` file and replaced each
cross-reference with a slug link, resolved against the practice's actual
content, not just its printed number (see "Four Citations Were Simply
Wrong," next). Two mechanical checks in
[`tools/verify_harness.py`](../tools/verify_harness.py) hold this going
forward: `check_no_bare_numeric_citations` fails if a bare `practice N`
citation reappears in body prose, and `check_slug_link_integrity` fails if a
`[slug](slug.md)` link points at a slug that does not exist — i.e. the
numbered check-citation-integrity's the plan's Migration section asked for,
recast in the form citations now actually take.

**Link path, and why `PRACTICES.md` needed a build-time rewrite.** A link
inside `practices/<slug>.md` written as `[other-slug](other-slug.md)` is
correct relative to that file's own directory. The same text is also reused
verbatim to compose the root-level `PRACTICES.md` catalogue view (via
[`tools/split_practices.py`](../tools/split_practices.py)'s `cmd_build()`),
where the same bare relative path would resolve one directory short. Rather
than write two different link forms into a practice's prose (which the
Migration section's own "no invented content" spirit argues against — the
*content* between the two documents must actually be identical prose, not
two hand-synced copies), `cmd_build()` now rewrites bare
`](sibling-slug.md)` links to `](practices/sibling-slug.md)` while composing
`PRACTICES.md` — a mechanical path adjustment for the embedding document's
location, not a content change.

**Four citations were simply wrong**, found while resolving each one against
its target's actual content rather than trusting the printed number — the
same kind of upstream data defect [FIXUP_39](#a-genuine-upstream-finding)
already documented, not something this sweep introduced:

- [`engine-plus-host-shims.md`](../practices/engine-plus-host-shims.md) and
  [`one-formatter-per-quantity.md`](../practices/one-formatter-per-quantity.md)
  and
  [`permutation-frontier-column.md`](../practices/permutation-frontier-column.md)
  each cited "practice 44 (shared renderer)" / "(sortable render)" / "(the
  render layer …)" — but practice 44 is *two named check levels*; the shared
  renderer is practice 46, `tabular-shared-renderer`. All three now link
  there. (Three independent citations landing on the same wrong number,
  never the topic they described, reads as an old renumbering that never
  got swept — exactly the failure mode slugs exist to end.)
- [`tabular-shared-renderer.md`](../practices/tabular-shared-renderer.md)
  itself cited "practice 12 (conventions harden into audits)" — practice 12
  is *every reply links the files it touched* (`reply-links-files`); "a
  convention hardens into an audit" is practice 6,
  `convention-to-audit`. Fixed.
- [`second-pass-capture.md`](../practices/second-pass-capture.md) cited
  "(practice 2)" for "decisions queued in the typed TODO" — practice 2 is
  the *orientation map*; the TODO is one of the three living documents named
  in practice 1, `repo-is-memory`. Fixed.
- [`affordance-is-shared.md`](../practices/affordance-is-shared.md) cited
  "practice 42(b)" for "compute the term whose direction is the point" —
  `verify-decomposition` (42) is the right practice, but that description
  matches its **(a)** sub-point (assert on the decomposition, compute terms
  directly) rather than **(b)** (a negative result is a parameterisation).
  Changed to `(a)`; lower confidence than the other three, since it is a
  sub-point call rather than a wrong practice, flagged here rather than
  silently decided.

None of these were introduced by the phase-1 conversion — the converter's
"move only" rule carried the wrong numbers forward exactly as BestPractice
had them, and the previous numeric-only citation-integrity check could only
confirm a cited number *existed*, not that it was the *right* one. Resolving
every citation against real content, which the link form forces a person or
session to do at read time, is what surfaced them.

**What this changes about `check_byte_identical_regeneration`.** Phase 1's
version of that check compared `cmd_build()`'s output against BestPractice's
*original, frozen* pre-conversion `PRACTICES.md` text (modulo two named,
approved exceptions) — a one-time proof that the mechanical split lost and
invented nothing, which already landed and is preserved in git history. This
sweep is a deliberate content edit on top of that already-proven split
(replacing citation text, not moving-or-dropping it), so a rebuild now
differs from that frozen snapshot by design — the frozen-original check
would fail forever from here on, on every future legitimate edit, which
defeats its purpose as an ongoing gate. The check now asserts the check's
real long-run meaning instead, matching the Migration section's
"byte-identical regeneration … a hand-edited view fails": `PRACTICES.md` on
disk must equal `python3 tools/split_practices.py build`'s current output,
full stop — i.e. `PRACTICES.md` is a generated view of `practices/*.md`, not
a second place to hand-maintain. Regenerate it (`build > PRACTICES.md`)
after any `practices/*.md` edit.

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
- **`tier` is `on-demand` for all 52; `severity` is `default` for all 52.**
  Choosing which practices are resident is explicitly phase 2 work (Sequence
  row 2: "Resident block within budget") — curating it now, before the
  budget mechanism that phase 2 builds exists to enforce it, would be
  guessing at a number nothing checks. `severity`'s only real job
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
(`FIXUP_39_MARKER`), and `tools/verify_harness.py`'s byte-identical-
regeneration check treats exactly that removal — and a single stray blank
line between practices 40 and 41, also pre-existing and whitespace-only —
as the two sole approved exceptions to an otherwise-exact diff against the
original. Worth reporting upstream at the next real check-in (phase 7 territory,
or sooner if Alex wants to hear about it before then); not fixed upstream
by this session, which only has read access to `alex137/bestpractice`.

## Tooling

- `tools/split_practices.py split` — `PRACTICES.md` → `practices/*.md`.
- `tools/split_practices.py build [--diff]` — the reverse, for the
  byte-identical-regeneration check.
- `tools/verify_harness.py` — runs every check from the plan's verification
  harness that is meaningful before phase 2 (loader) and phase 3 (multiple
  sources) exist; the rest report as not-yet-applicable, not as passed.
- `tools/precedent_show.py SLUG... [--why|--story|--install]` — the one
  code path an agent (or a human) uses to load a practice; never read
  `practices/*.md` directly.
