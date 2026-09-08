---
slug:        constants-are-risk-inputs
title:       Undecided operating constants are risk inputs, not doctrine
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a model, study or comparison table rests on an operating constant nobody decided — a margin, a cap, a rate, a floor"
gates:       []
index_clause: "a constant nobody decided is a swept, registered input -- never doctrine"
checked_by:  null
defines:     ["conservative corner", "bet-relevant"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Alex, 2026-09-08 — merged on main as catalogue entry 54, a check-in from dependent repo #1"
source_practice_number: null
---
## Rule
No operating constant in a model carries settled status by label. A number
nobody has decided — a margin, a cap, a rate, a floor that was picked because
it felt plausible and then hardened by repetition — is an **assumption**, and
it stays visible as one: an explicit, swept, risk-labeled *input* rather than
a buried default. Three mechanics:

- **A register** lists every such constant with its as-built value, the lever
  it carries (from a sweep, not a guess), where it lives, and its disposition.
  Two classes: settings whose stakes are safety or capability and that only a
  field test can decide (the **bet-relevant** class), and banded
  hardware/operations settings whose stakes are cycle time or kit sizing.
  Constants that are calibrated physics or sourced hardware are listed as
  *explicitly excluded*, with the reason, so the boundary is itself
  reviewable.
- **A comparison table** built on such constants evaluates every row at the
  **conservative corner** of the bet-relevant class (the default basis for any
  frontier or ranking) and prints the **aggressive corner beside it**. A row
  whose case closes conservatively is robust; a row viable only at aggressive
  settings is marked as a test bet, not a build bet.
- **A guard** in the model audit: a module-level constant whose attached
  comments claim a settled status (words like *doctrine*, *as built*,
  *settled*) must be named in the register — as a risk input, a banded
  setting, or an exclusion — or carry an explicit opt-out marker with a
  reason. A constant leaves the register only by a dated, named decision or a
  test result, recorded with its evidence.

## Detail
The tell is a tuning constant wearing a settled-sounding name — *doctrine*,
*baseline*, *standard* — with no recorded decision behind it. Such a constant
is an assumption in uniform: nobody re-opens it, because the name says
someone already decided, and nobody did.

Splitting *settings the built article can still change* from *choices baked
into the build* is what makes the two corners useful. The former are envelope
explorations, the latter are the actual bet, and the table should show which
rows survive if the former stay conservative.

## Why
The favorable-lever clause in
[verify-decomposition](verify-decomposition.md) catches a settled-sounding
constant *when someone happens to question it*; this practice removes the
class. The failure it prevents is quiet and expensive: a capital decision —
which configuration to build — gets made on a table whose numbers depend on
operating settings no one chose, so the bet silently inherits an
aggressiveness nobody signed for, and the first field test discovers it.

## Story
A program preparing to commit real money to a configuration found that its
headline capability figure moved by a quarter on one flight-operations cap
that had been "picked as plausible" and labeled doctrine. An inventory found
a second such number on the same gate and, once a mechanical guard existed,
four more it had missed by hand — including the utilization figure dividing
every unit cost in the study. The owner's direction became the rule: *"we
don't have doctrine about numbers."*

## Install
Create the register next to the models it governs; add the guard to the model
audit ([tools/model_audit.py](../tools/model_audit.py)'s
`check_constants_register`, which a host arms by pointing
`CONSTANTS_REGISTER` at the register's repo-relative path — comment-attached
settled words then have to be registered or opted out with a reason, and
preceding comment blocks are attributed at column zero only so a previous
constant's indented trailing comment cannot false-fire); make the
conservative corner the frontier basis in any comparison table; route
retirement of a constant through a dated decision record.
