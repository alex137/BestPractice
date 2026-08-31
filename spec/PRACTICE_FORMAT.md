<!-- Last updated: 2026-08-31 (Buenos Aires) by a phase-0/1 build session, to version 1 -->

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
- **`tier` was `on-demand` for all 52 at phase 1; phase 2 curated 7 to
  `resident`** once the budget mechanism existed to enforce the choice —
  see [spec/LOADER.md](LOADER.md) for which seven and why. `severity` is
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
