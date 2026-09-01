---
slug:        verify-decomposition
title:       Verify the decomposition, not the total — and never encode an impossibility
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "trusting a model's total without checking its parts"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 42
---
## Rule
**The practice.** A model earns trust through how it is built, not through whether
its answer looks reasonable. Two failure modes exploit the gap, and both are
invisible to the checks people usually run.

**(a) A plausible total can hide errors that cancel.** If one term is omitted and
another is over-counted, the sum can land in exactly the range you expected, and
every downstream figure will look sane. Re-running the model does not help: it
reproduces its own assumptions faithfully, including the wrong ones. Nor does
tightening the tolerance on the output — the output was never the problem.

The tell is a headline number that survived several passes without anyone
re-deriving the *parts*. Ask what each term physically pays for, and whether
anything is charged twice or not at all: a shared budget spent by two consumers,
work computed over the wrong path length, an actor whose own cost was never
booked because the analysis was framed around the other actor.

**Two things fix it, and only the second is reliable:**

1. **Assert on the decomposition.** Write checks that each term is *present* and
   behaves correctly — this quantity must be non-zero whenever those two differ,
   that path must exceed this one, this cost must be zero below a threshold and
   rise past it. Checks on the total pass happily while the parts are wrong.
2. **Derive it a second time, independently, and keep that derivation.** Hand
   arithmetic where a closed form exists; a separately written integration where
   it does not. Cancelling errors are exactly the class that only a second,
   differently-structured derivation catches. Commit it as a harness rather than
   discarding it — the errors it catches recur, and a review that lives in
   someone's scratch directory protects nothing.

**(b) A negative result is often a parameterisation, not a property.** A model
answers the question its constants encode. If the levers that would relieve a
constraint are hard-wired to baseline values, the model can only ever report the
blocked case — and prose then promotes one parameterisation into a law of
nature. *"X is impossible"* becomes the finding when the truth was *"X is
impossible with these particular settings."*

The tell is a negative conclusion stated without a sensitivity beside it. Before
writing that something cannot be done, vary the inputs that would relieve it and
report the boundary instead: the conclusion is nearly always *"blocked here,
available there,"* which is far more useful than a flat no.

**Never encode an impossibility as an assertion until you have done that.** A
check that asserts a negative locks the error in as an invariant and defends it
against the next person who suspects otherwise — converting a soft mistake into
a hard one, and putting the burden of proof on whoever is right.

**Related:** [check-source-architecture](check-source-architecture.md) (an option you invented is not a baseline) is the same
family one level up — there the *framing* is unexamined rather than the terms.

## Why

## Story

## Install
