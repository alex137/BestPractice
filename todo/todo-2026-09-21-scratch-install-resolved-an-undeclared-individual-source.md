---
slug:              todo-2026-09-21-scratch-install-resolved-an-undeclared-individual-source
kind:              manual
domain:            engine
severity:          medium
status:            closed
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "A -- an individual set is additive BY DESIGN and goes into every project; the generated block now discloses it"
decision_strength: decided
waiting_on:        null
noted:             2026-09-21
closed:            2026-09-21
---
## What

**A project whose `precedent.json` declares only `universal` and
`repo-local` resolved an INDIVIDUAL source anyway.** Measured in a scratch
install on 2026-09-21: run it as the session's own environment stood, and
[precedent_sync_views.py](../tools/precedent_sync_views.py) reports *"materialized 142 practice(s), 15 check
script(s)/test(s) and 3 harness adapter(s)"*. Run the same command in the
same tree with `HOME` pointed at an empty directory and every `PRECEDENT_*`
variable unset, and it reports **125 practices, 1 check, 0 adapters** —
and says plainly *"precedent resolve: no individual source resolved."*

Seventeen practices, fourteen check scripts and three harness adapters,
from a source the project never declared.

## Why It Matters

Two different things, and only the first is arguably a feature:

1. **A session's own machine leaks into a project's generated views.** The
   individual source is resolved through a user-level config
   (`~/.config/precedent/config.json`), not through the project's
   declaration. So [AGENTS.md](../AGENTS.md), `practices/` and `tools/checks/` in that
   project are a function of *who ran the install*, not of what the
   project declares. Two people installing the same project get different
   trees.
2. **It masks other findings.** It is exactly what hid
   [todo-2026-09-21-two-tools-generate-agents-md-and-disagree.md](todo-2026-09-21-two-tools-generate-agents-md-and-disagree.md)'s
   real one-line cause behind a large alarming diff. A check whose output
   depends on ambient state is a check that cannot be read.

## What Has NOT Been Established

**Which of these it is**, and that is the whole item:

- The user-level config is *meant* to be additive — an individual's
  practices follow them into every project they touch, by design — and the
  only defect is that nothing says so out loud in the project's own
  generated header.
- Or the project's `sources` list is meant to be exhaustive, and the
  user-level config reaching past it is a real scoping bug.

Nobody has read `precedent_resolve.load_config()` against the design
intent to say which. **Do that before proposing a fix** — the two answers
have opposite remedies, and guessing picks one.

## What Would Close It

An answer to the above, written down, plus whichever follows from it:

- If additive by design: the generated block's own header names the
  individual source and its practice count, so a reader can see the tree
  is machine-dependent rather than discovering it from a diff.
- If a scoping bug: the project's declared `sources` constrain resolution,
  and an undeclared source is a NOTICE on stderr rather than 17 silent
  practices.

## Disposition (2026-09-21)

**Stays filed rather than worked now.** Morgan: *"approved on the first"* —
agreeing to the session's own proposal that this sit in the repo until it
is worth the read, which is `assented`, not `decided`
([decision-strength](../practices/decision-strength.md)).

Nothing here is time-sensitive: the contamination is visible whenever
somebody regenerates in a project and compares practice counts, and the
one bug it actually masked is fixed. What it costs while it sits is
readability of a diff, not correctness of a tree.

## Answered (2026-09-21) — Option A, Decided

Morgan, choosing from the two options laid out: *"A -- precedent-individual
goes into ALL your projects."* Quoted, so `decided`, not `assented`
([decision-strength](../practices/decision-strength.md)) — this supersedes
the `assented` recorded an hour earlier, when the item was only being left
filed.

**So the resolution was never reaching past anything.** An individual set
resolves through the machine's user-level config on purpose: a person's own
practices follow them into every project they touch, which is the whole
reason to have one. The project's `sources` list constrains the sources the
PROJECT declares; it was never meant to be the complete list of what binds a
session.

**The defect was the silence, and that is fixed.** The generated loader
block now names how many practices came from an individual source and says
plainly that the tree is machine-dependent — in the projects where that is
true, and nowhere else. A repo with no individual practice in force (this
one, every public set, every CI checkout) renders byte-identical to before.
Both renderers emit it, because both call the same
`build_loader_block()`.

**The precise numbers, since two of them are right about different things.**
Measured in the scratch install:

- **18** practices resolve from the individual source.
- The catalogue total rises by **17**, from 125 to 142, because one of the
  18 (`session-title-names-the-difference`) SHADOWS a universal slug rather
  than adding to it.

Earlier notes in this thread said 17 without that distinction.

**The other half of the answer is documentation**, because "it goes
everywhere" is only half useful without "so where does a rule for SOME
repos go":
[documentation/SHARED_PRACTICE_SETS.md](../documentation/SHARED_PRACTICE_SETS.md),
new, with the sorting question stated in one line — *do you want this rule
in every project you touch?* — and cross-linked from both the technical and
the non-technical guide.
