---
slug:        environment-gotchas
title:       "Recorded lore: environment gotchas with their stories"
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "hitting an environment or tooling quirk"
gates:       []
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 4
---
## Rule
Every expensive environment discovery (a package that must be installed, a
tool that silently doesn't work, a path that does work) is written down **with
the story of what failed and why, not just the fix**, and a "do NOT rediscover
these" section in the instructions file is where a session finds it.

**When the stories outgrow what every session can afford to load, split them.**
The section then keeps **one line per trap** — the symptom, and a link — and
the stories move to a linked record, in full. A split changes the loading,
never the text.

## Detail
**Start unsplit.** A handful of entries belongs inline, where nothing has to be
clicked: the index only pays for itself once the section is large enough that
every session is carrying stories it will not read.
[session-load-budget](session-load-budget.md) is what tells you — the split is
one of the moves that rule's reduction pass reaches for, and the trigger is a
measured ceiling, not a feeling that the file is long.

**What the index line has to carry is the SYMPTOM**, in the words a session
would use for what it is seeing — not the name of the fix. A session scanning
the index has not diagnosed anything yet; it is matching what is in front of it
against a list. An entry whose line reads *"use `git cat-file -e`"* is
unfindable by the session that needs it.

**The story stays whole on the other side of the link.** Moving an entry is not
an occasion to shorten it, and a record that quietly became a summary has given
up the thing the split was supposed to protect.

## Why
**The fix alone is a fact a later session cannot judge.** Told only "install this package", a session that finds the package already present, or the symptom slightly different, has no way to decide whether the note still applies — so it either works around a note that is still correct, or trusts one that has gone stale. The story is what makes the note re-judgeable.

The cost being defended against is unusual in that it is paid in *confusion* rather than in breakage. A tool that fails with a misleading error does not announce that the environment is at fault, so a session spends its time on the wrong hypothesis and reaches a plausible wrong conclusion. That is expensive, invisible in the diff, and repeats exactly as often as the environment is rebuilt.

## Story
A build tool once failed on every input with a misleading error; two
full sessions were lost to "this tool is broken" lore before someone found the
one missing package. Once the fix *and the story* were written down, the
failure never recurred — and the story is what lets a future session judge
whether the note still applies.

## Install
A gotchas section in the instructions file
([templates/AGENTS.md.template](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/AGENTS.md.template)), plus
[session-bootstrap](session-bootstrap.md) (encode the fixes as a bootstrap hook so they apply themselves).

The split shape, once a repo needs it, is a `record/GOTCHAS.md` holding the
entries in full and the section holding one linked line each —
[upstream's own](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS.md)
is the worked example. `tools/precedent_check.py` follows whichever shape it
finds: unsplit, it reads the section's own entries; split, it follows the links
and applies the same story test to the record.
