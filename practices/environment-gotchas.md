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
Every expensive environment discovery (a package that must be
installed, a tool that silently doesn't work, a path that does work) is
written into a "do NOT rediscover these" section — with the story of what
failed and why, not just the fix.

## Detail

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
([templates/AGENTS.md.template](../templates/AGENTS.md.template)), plus
[session-bootstrap](session-bootstrap.md) (encode the fixes as a bootstrap hook so they apply themselves).
