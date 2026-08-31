---
slug:        layered-practice-packs
title:       Layered practice packs: a domain layer between generic and repo-local
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "deciding where a new rule belongs"
index_clause: "generic, domain, repo-local \u2014 each rule to its own layer"
checked_by:  null
defines:     ["practice pack"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 23
---
## Rule
Rules come in three scopes, and each gets its own home. **Generic** rules
(true of any repo) live in this upstream and its instantiations.
**Repo-local** rules (true only of one repo's subject matter) live in that
repo's instructions files and never leave. Between them sit **domain** rules
— true of any repo running the same *kind* of program (a compliance regime,
a lab workflow, a regulated-filing process) but meaningless outside it.

The decision rule for any new rule: *would this hold in an unrelated repo?*
→ upstream (public scrub applies). *Only in another repo running the same
kind of program?* → the pack. *Only here?* → repo-local.

## Detail
Those are collected into a **practice pack**: a vendored tree at
`process/<pack>/` with the same anatomy as this upstream (a practices
catalog, an install playbook, extracted tools, harness adapters), tracked by
its own manifest at `process/manifest_<pack>.json` with its own optional
scrub blocklist, audited by the same `practice_audit.py` (it discovers every
`process/manifest*.json`). A pack may **route**: its harness adapter (e.g.
an agent skill) declares when the domain's rules apply, so an agent loads
them exactly when doing that domain's work instead of carrying them in every
session.

## Why

## Story
A domain program inside a dependent repo accumulated rules that
were neither generic (they could not be published, and their vocabulary was
all domain) nor repo-local (a second program of the same kind would need
every one of them). With no home of their own they lived interleaved with the
repo's local rules, which meant every session carried them whether relevant
or not, and a future split of the program into its own repo would have meant
re-deriving which rules travel. Vendoring them as a pack made the split a
`git mv` instead of an archaeology project — the same pre-split shaping that
made this upstream's own extraction clean.

## Install
Vendor the pack tree at `process/<pack>/`; write
`process/manifest_<pack>.json` (schema of [INSTALL.md](INSTALL.md) §5, plus
`upstream.scrub_blocklist` — a path, or `null` to opt a private pack out of
the scrub); instantiate the pack's practices in the repo's real files and
record the mapping; install its harness adapter so the rules load when the
domain work happens. The export gate (practice 14) covers packs too: a thread
that improves a domain practice folds the abstracted form into the pack tree
in the same branch, keeping repo vocabulary out per the pack's blocklist.
