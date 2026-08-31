---
slug:        engine-plus-host-shims
title:       Exported tools are one engine plus host shims
tier:        on-demand
severity:    default
applies_to:  ["process/upstream/**", "templates/harness/**"]
occasion:    "exporting a tool across a repo boundary"
gates:       []
index_clause: "one vendored engine, thin host shims, never a fork"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 50
source_rule_unlabeled: true
---
## Rule
A practice that ships tooling (a renderer, a lint, a sync gate) crosses the
repo boundary as **code plus config**, split on one line: **domain-neutral
mechanism lives in the vendored upstream tree and is the single
implementation; everything host-specific — registries, vocabulary, index
names, scan scopes — lives in a thin shim in the host repo** that loads the
vendored module, sets its configuration attributes, and delegates. The
practice text carries the behavior contract (the numbered spec of what the
tool delivers), which is also what lets a host on a different stack
reimplement deliberately rather than accidentally.

## Detail
**The rule of thumb for what goes where:** if a change would be wanted by
every repo using the tool, it is engine — edit the vendored file, and it
ships upstream at the next check-in; if only this repo would want it, it is
config — edit the shim. A new check, a new interaction, a bug fix: engine.
A new document registered, a new stopword, a different default branch:
shim.

## Why
**Why not a fork.** A host that copies the tool and edits its copy is
running two implementations synced by hand. The vendoring audit's drift
hashes will nag, but every improvement is edited twice, and the copies
diverge the first time someone forgets. (Origin: the first dependent repo
maintained renderer, lint, and sync-gate forks in lockstep through one day
of heavy feature work — every change patched twice — then collapsed all
three to shims; behavior was verified identical before and after, the
renderer's output byte-for-byte, and ~1,400 lines of duplicate
implementation disappeared. The collapse also surfaced a latent bug: the
exported sync-gate copy referenced a config name no one had ever defined,
because nothing had ever executed it.)

**Why not spec-only.** A tool's value is its accumulated behavioral detail
— the numeric sort keys that survive currency suffixes, the filter that
survives a column move, the false-positive guards on a check. A dependent
repo reimplementing from prose gets a different-in-a-hundred-ways tool and
re-learns every lesson. Spec and code are not competitors: the spec is the
contract, the vendored code is the reference implementation, and a repo
that can run it should never be writing its own.

## Story

## Install
Vendored tool with module-level configuration attributes and
sane defaults; host shim of a dozen lines (load via an explicit file path
under a distinct module name to avoid shadowing, set attributes, delegate
to the engine's entry point); the manifest entry notes shim status so the
vendoring audit tracks the engine, not the shim. Every host-side runbook
keeps invoking the shim path — the restructure changes no workflows.

**Related.** Practice 44 (shared renderer) and practice 19 (generated-block
sync) are the worked examples; practice 33's "transformations live in code"
is the same instinct one level up; the check-in flow of the vendoring
playbook is how engine changes propagate.
