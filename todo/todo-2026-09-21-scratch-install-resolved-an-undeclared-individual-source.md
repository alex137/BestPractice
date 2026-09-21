---
slug:              todo-2026-09-21-scratch-install-resolved-an-undeclared-individual-source
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "stays filed; answer it when it is worth the read, not now"
decision_strength: assented
waiting_on:        null
noted:             2026-09-21
closed:            null
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
