---
slug:        environment-gotchas
title:       Recorded lore: environment gotchas with their stories
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "hitting an environment or tooling quirk"
checked_by:  null
defines:     []
status:      active
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

## Why
A build tool once failed on every input with a misleading error; two
full sessions were lost to "this tool is broken" lore before someone found the
one missing package. Once the fix *and the story* were written down, the
failure never recurred — and the story is what lets a future session judge
whether the note still applies.

## Story

## Install
A gotchas section in the instructions file
([templates/AGENTS.md.template](templates/AGENTS.md.template)), plus practice
13 (encode the fixes as a bootstrap hook so they apply themselves).
