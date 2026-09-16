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
tool that silently doesn't work, a path that does work) is written down
**with the story of what failed and why, not just the fix**, in its own
file — one trap, one file, forever — under `gotchas/gotcha-<date>-<slug>.md`
(directory and frontmatter shape:
[spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
Part 2).

**None of that catalogue loads into the instructions file, at any size.**
The instructions file carries a short pointer instead — hit an unexplained
failure, grep `gotchas/` before concluding it's new — never the stories,
and never even a one-line-per-trap index. A generated overview (symptom
plus link, one line per live entry) exists for the deliberate read; nothing
loads it automatically.

## Detail
**Every entry is its own file from the first one.** There is no size below
which stories live inline "for now": the instructions file never carries
the catalogue, so there is nothing to gain by deferring the split, and a
repo with two gotchas is exactly as split as one with two hundred.

**What a session searches on is the SYMPTOM**, in the words a session would
use for what it is seeing — not the name of the fix. Lead the entry's own
`## Symptom` section with it, so a grep on the failure text actually lands:
an entry keyed only on *"use `git cat-file -e`"* is unfindable by the
session that needs it and never typed that phrase.

**The story stays whole in its own file.** Retiring an entry is not an
occasion to shorten it — flip `status: retired` in place; nothing is ever
deleted or trimmed on its way out, and nothing moves.

## Why
**The fix alone is a fact a later session cannot judge.** Told only "install this package", a session that finds the package already present, or the symptom slightly different, has no way to decide whether the note still applies — so it either works around a note that is still correct, or trusts one that has gone stale. The story is what makes the note re-judgeable.

The cost being defended against is unusual in that it is paid in *confusion* rather than in breakage. A tool that fails with a misleading error does not announce that the environment is at fault, so a session spends its time on the wrong hypothesis and reaches a plausible wrong conclusion. That is expensive, invisible in the diff, and repeats exactly as often as the environment is rebuilt.

**A one-line index is a smaller version of the same cost, not a different one.** It is cheaper per entry than the full story, but it is still a fixed tax that grows every time a trap is caught, paid by every session whether or not that session is debugging anything that day. Moving the stories out and leaving the index behind fixes the first-order problem and recreates the second-order one at a smaller constant — which is exactly what happened here: BestPractice's own index reached 44 lines before anyone measured what it cost at the top of every session.

## Story
A build tool once failed on every input with a misleading error; two
full sessions were lost to "this tool is broken" lore before someone found the
one missing package. Once the fix *and the story* were written down, the
failure never recurred — and the story is what lets a future session judge
whether the note still applies.

The index that replaced the inline stories was itself still loaded whole,
every session, forever — one line per trap, with no ceiling. It reached 44
lines in BestPractice's own AGENTS.md before a session totaling what gets
paid before any real work starts found several thousand tokens spent on
traps most sessions never touch. The index moved out into a generated,
not-loaded overview (2026-09-16); the instructions file kept only a pointer
and a grep instruction.

## Install
A short pointer section in the instructions file naming `gotchas/` and the
grep instruction — no entries, no index — plus
[session-bootstrap](session-bootstrap.md) (encode the fixes as a bootstrap
hook so they apply themselves). One file per trap under
`gotchas/gotcha-<date>-<slug>.md`;
[tools/build_gotcha_index.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/build_gotcha_index.py)
generates
[gotchas/INDEX.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/gotchas/INDEX.md)
for the deliberate read from those files' frontmatter and `## Symptom`
sections.

[tools/precedent_check.py](../tools/precedent_check.py)'s
`environment-gotchas` check reads `gotchas/*.md` directly and applies the
story test to each `status: live` entry's Symptom and Story — it does not
read the instructions file's pointer at all, only that the catalogue exists
and no live entry is a bare fix.
