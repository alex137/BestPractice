---
slug:        layered-practice-packs
title:       Layered practice packs: a domain layer between generic and repo-local
tier:        on-demand
severity:    default
applies_to:  ["practices/**", "PRACTICES.md", "precedent.json"]
occasion:    "deciding where a new rule belongs"
gates:       []
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
kind of program?* → domain-scoped, on-demand (see Detail). *Only here?* →
repo-local.

## Detail
**Superseded, 2026-09-01, for any repo running Precedent's loader: the
vendored-pack mechanism.** This practice originally routed domain rules by
collecting them into a **practice pack** — a separate vendored tree, with its
own manifest, its own scrub blocklist, and a harness adapter that decided
when to load it (kept below for a repo that has not migrated). Under
Precedent's loader (`PRACTICE_ENGINE_PLAN.md`, "How an Agent Knows Which
Practices to Load"), that machinery is redundant: a domain rule is simply a
practice — Universal or Team — whose `applies_to` / `occasion` / `gates`
scope it to that domain's work, routed by the same occasion index and
path-triggered channel as every other on-demand practice. The decision rule
above still holds; only the *implementation* of the middle tier changed.
Recorded in [CHANGES_TO_TELL_ALEX.md](CHANGES_TO_TELL_ALEX.md).

**Still open, not solved by the loader: a domain bundle shared across more
than one team.** The loader routes a single source's own practices; it does
not give a domain's rules a home independent of any one team's roster, which
a compliance- or lab-workflow domain used by several different teams would
need. Tracked in `PRACTICE_ENGINE_PLAN.md`'s Deferred section, merged with
"a practice belonging to more than one team" — the same underlying gap seen
from the other direction.

**The pack mechanism, for a pre-migration consumer repo.** Domain rules are
collected into a **practice pack**: a vendored tree at `process/<pack>/` with
the same anatomy as this upstream (a practices catalog, an install playbook,
extracted tools, harness adapters), tracked by its own manifest at
`process/manifest_<pack>.json` with its own optional scrub blocklist, audited
by the same `practice_audit.py` (it discovers every `process/manifest*.json`).
A pack may **route**: its harness adapter (e.g. an agent skill) declares when
the domain's rules apply, so an agent loads them exactly when doing that
domain's work instead of carrying them in every session.

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
**On Precedent's loader:** write the domain practice as an ordinary Universal
or Team practice file, with `applies_to` / `occasion` / `gates` scoping it to
the domain's work. Nothing else to install — it is routed the same way as
every other on-demand practice.

**Pre-migration (a repo still vendoring BestPractice the old way):** vendor
the pack tree at `process/<pack>/`; write `process/manifest_<pack>.json`
(schema of [INSTALL.md](INSTALL.md) §5, plus `upstream.scrub_blocklist` — a
path, or `null` to opt a private pack out of the scrub); instantiate the
pack's practices in the repo's real files and record the mapping; install its
harness adapter so the rules load when the domain work happens. The export
gate ([practice-export-loop](practice-export-loop.md)) covers packs too: a thread that improves a domain practice
folds the abstracted form into the pack tree in the same branch, keeping repo
vocabulary out per the pack's blocklist.
