---
slug:        name-both-sides-of-ledger
title:       A computation that books a transfer names both sides of the ledger
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a computation books a transfer between two parties"
index_clause: "name both sides; check what is charged against what is received"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 52
source_rule_unlabeled: true
---
## Rule
The rule: any closed-form gate or feasibility formula that books a
transfer must **(a) name its sources and sinks explicitly** — every
account the quantity can come from and every account it can land in —
and **(b) carry a property self-check asserting the whole-system
inventory closes**, sources equal to sinks within the model's stated
noise. Where an independent integrator or simulation exists, calibrate
the closed form against it and assert the band; where none exists, a
one-line back-of-envelope inventory (is the payer's total available
even of the right order against the sink side?) belongs in the
derivation's comment.

## Detail
When a model charges one party for what another receives — work for
kinetic energy, spend for inventory, a debit for a credit — the
plausibility check everyone naturally runs is *"does the charge equal
the recipient's gain?"* That check is the trap, not the verification:
**the recipient-side ledger balances by construction.** Charging a
force over the recipient's displacement always yields exactly the
recipient's gain; charging a spend against the goods received always
matches the goods. What that one-sided check can never see is the
term between the parties — dissipation, friction, spoilage, fees —
which the payer also pays, over the **payer's own path**.

## Why
**Why review misses it.** Two compounding effects, both observed in
the origin incident. First, the wrong length is usually the *salient*
one: the mechanism's narrative stars one displacement (the relative
motion, the visible stroke), and that is the length at hand when the
formula is written — while the work integral belongs on the payer's
displacement. Second, direction-of-motion bias: when the erroneous
formula lands inside a commit that is correcting a known error in the
*opposite* direction, the overshoot wears the correction's clothes —
big new numbers read as the fix working. Neither reviewer instinct
(does the charge match the gain? does the change move the right way?)
catches a factor hidden in the dissipation term.

## Story
**Origin.** A feasibility gate charged a hauling agent's energy cost
as force × the *load's* displacement rather than the agent's own
path — exactly half, the other half leaving through a dissipative
element between them. The halved charge equaled the load's
kinetic-energy gain to the digit, so the one-sided check passed; the
published capability ceiling came out ~2× optimistic (compounded by a
missing geometric completion condition the same 1-D framing hid) and
survived its thread's otherwise-careful review because it arrived in
a commit raising ceilings a doctrine reread had shown were wrongly
zero. It was caught a day later only when an independent
trajectory integrator's whole-system energy balance refused to close —
and a three-line inventory then showed the payer's entire available
energy was ~3× short of the sink side at the published ceiling. The
correct accounting had existed in the program's own prose for weeks,
written down and executable nowhere — the same lesson as the
model-audit practice, recurring: prose does not fail a build; a
ledger assertion does.

## Install
