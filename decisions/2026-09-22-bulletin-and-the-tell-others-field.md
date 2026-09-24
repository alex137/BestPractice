---
date: '2026-09-22'
question: |
  spec/CHANGES_TO_TELL_ALEX.md was written for one reader and one event —
  Alex, before the branch merged back to main. Alex has seen it, so that
  job is done. Morgan asked whether the file should become something
  standing instead: a place recording the important recent changes other
  people and agents should know about. If so, what feeds it, what keeps it
  from becoming noise, and what is it called?
decision: |
  Build it, as a GENERATED view rather than a hand-maintained document, at
  `BULLETIN.md` in the repo root.

  Fed by an optional frontmatter key, `tell_others:`, on the three kinds of
  file that are already written at the moment the news exists —
  `practices/*.md`, `decisions/*.md`, `gotchas/*.md`. One sentence, or the
  literal value `none`. The generator renders a summary-and-link list over a
  rolling 30-day window.

  FOUR ANTI-NOISE RULES, which are the substance of the decision and not
  decoration:

  1. The bar is behavioural, not a judgment of importance: "would someone
     who already knows this repo do something DIFFERENT tomorrow because of
     this?" If no, the value is `none`. A rule that changed meaning: yes. A
     rule retired: yes. A new rule that writes down what everyone already
     did: none. A gotcha: `none` by default.
  2. `tell_others:` is required to be PRESENT, never required to be
     non-empty. `none` is the common, expected answer. This forces a
     decision rather than a sentence, and is what stops the file both from
     filling with noise and from sitting permanently empty because nobody
     is sure what qualifies.
  3. The rendered file is capped at 7 entries, ranked: retired or
     superseded practice > changed practice > new practice > decision >
     gotcha. Overflow is DROPPED, never appended. A file that cannot grow
     past 7 cannot become a changelog.
  4. A `tell_others:` value longer than ~140 characters is rejected
     mechanically, so it cannot become prose.
  5. **Newest first.** The file renders in reverse chronological order, most
     recent entry at the top, so the reader meets what changed last without
     scrolling. The cap in rule 3 therefore drops the OLDEST entries, which
     is the behaviour that makes a capped file readable rather than
     arbitrary (Morgan, 2026-09-22).

  [spec/CHANGES_TO_TELL_ALEX.md](../spec/CHANGES_TO_TELL_ALEX.md) is
  closed rather than deleted: its status
  becomes `closed` with its dates stated on its face, its generated figures
  are frozen as a measurement of the day it closed, and it is deregistered
  from `doc_sync` so nothing keeps editing a document that says it is no
  longer updated (Morgan, 2026-09-22).

  Every existing practice, decision and gotcha is backfilled with
  `tell_others: none` so the presence check can be unconditional — as its
  own commit, separate from the mechanism, so the mechanism's diff stays
  reviewable.
alternatives: ["Retire the file and rely on well-written fold-in pull
                request bodies, which already have a named audience and a
                natural deadline — real, and cheaper, but loses the one
                sentence saying why a reader would care",
               "A hand-maintained file with a practice saying to keep it
                updated",
               "Generate it from existing frontmatter alone (status flips,
                strength, dates) with no new field — a viable v0, rejected
                because it gives WHAT changed and not why anyone cares"]
decided_by: Morgan
strength: decided
---

## Why a generated view and not a document

The original file worked because it had **one named reader and one
deadline**. Strip both and "the most important things others should know"
has no editor, and a file with no editor goes one of two ways: permanently
empty, or a second changelog nobody reads.

This repository has that failure mode on record twice.
[AGENTS.md](../AGENTS.md) went
29,443 to 71,059 bytes in three days. The engine plan went 56,675 to
108,557 on accumulated amendments — which is why
[decisions/](../decisions/) exists at all.

There are already four stores: `decisions/` for why a choice was made,
`gotchas/` for environment traps, `todo/` for open work, `practices/` for
the rules. A fifth prose file would restate all four and drift the day it
was written. **A generated index that only links cannot drift**, and the
mechanical check that it matches a fresh build is the same pattern
[tools/build_views.py](../tools/build_views.py) and
[tools/precedent_vocabulary.py](../tools/precedent_vocabulary.py) already
use.

The same reasoning rules out the obvious practice wording — *"remember to
update this file when something important changes."* An advisory rule is
exactly what fails here: on 2026-09-21
[practices/fixture-owns-its-state.md](../practices/fixture-owns-its-state.md)
was violated by code that **quoted it by name two lines above the
violation**. Putting the field on a file somebody is already writing, and
checking its presence mechanically, is the form that survives.

## Why the rolling window is not enough on its own, measured

A 30-day window was the first proposal. Counted against this repository's
actual rate on 2026-09-21: the last three days held **12 practices, 1
decision and 13 gotchas — 26 entries**, which extrapolates to roughly 200
in a 30-day window. (The 7- and 30-day counts are inflated by the phase-1
migration; the 3-day figure is closer to the real rate.)

**The window is a filter that does not filter.** Rules 1 and 3 above are
what take 200 down to something a person reads, and that is why `none`
being the ordinary answer is the design rather than a weakness in it.

## Why the name BULLETIN

Checked against the repository rather than chosen on taste. Every root
document here is a single capitalised word — [MAP.md](../MAP.md),
[GLOSSARY.md](../GLOSSARY.md), [PRACTICES.md](../PRACTICES.md),
[INSTALL.md](../INSTALL.md) — except
[WHERE_THINGS_ARE.md](../WHERE_THINGS_ARE.md).

**A bulletin is posted because somebody decided it should be read**, which
puts the selection in the word itself, and it implies short and periodic
rather than exhaustive. The word appears nowhere else in this repository,
so it carries no existing meaning to collide with and no software
convention.

Rejected, each for a checked reason rather than a preference:

- **`WHAT_CHANGED_LATELY`** — modelled on the one multi-word outlier
  instead of the house style, and asked the filename to carry a bar that
  belongs in the practice.
- **`KEY_UPDATES`** — Morgan's own first suggestion, and serviceable.
  "Updates" is the changelog-adjacent word: in a public repository other
  repositories vendor, it invites a stranger to expect a release log, and
  therefore invites exhaustive entries.
- **`BRIEFING`** — collides with an established term of art here:
  [practices/brief-it.md](../practices/brief-it.md) plus seven
  `spec/*_BRIEF.md` documents. A reader would have to distinguish "the
  brief" from "the briefing".
- **`NOTICES`** — `NOTICE` is an Apache-license convention in public
  repositories, so a stranger could reasonably expect license text; and
  "notice" already appears as ordinary prose across roughly thirty files
  here.
- **`MATERIAL_CHANGES`** — the closest runner-up, because *material*
  is precisely the bar in rule 1. Rejected as the most jargon-heavy
  option, against
  [practices/readers-vocabulary.md](../practices/readers-vocabulary.md).

## The reader, which decides how every entry is worded

**A session starting fresh in a repository that vendors this practice
layer** — someone who cannot ask a follow-up question. Morgan can skim
something written for that reader; that reader cannot unpack something
written for Morgan.

The generated file opens with a line saying what it is and is not, so the
changelog reading is closed off by the document rather than by its name:
*the few changes from the last 30 days that change what you should do — not
a changelog, and most changes never appear here.*

## Status

Adopted, not yet built. The implementation was handed to a separate
session on 2026-09-22. Nothing in this record is provisional: the name, the
field, the four rules, the window and the backfill are settled, and a
session implementing them is implementing, not redesigning.
