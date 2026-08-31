---
slug:        build-buy-decompose
title:       Build/buy: decompose before deciding, and keep the verdict supplier-independent
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "deciding whether to build or buy a component"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 35
---
## Rule
A build-or-buy question almost always arrives at the wrong
granularity — *"should we build this ourselves or get it from them?"* — and
answering it as posed produces a yes/no about a supplier when what was needed
was a map. Two moves, in order.

**First, decompose the thing being procured, and give each part its own
verdict.** The parts usually disagree, and the disagreement is the answer. The
diagnostic is blunt: **if your answer is a single yes/no, you probably have not
checked whether the thing has parts with different answers.** In the origin
case a four-way split turned "wrong supplier" into "right supplier, wrong
layer" — which is a usable answer, where a flat no would have closed a door
worth keeping open.

**Second, rest the verdict on ownership arguments rather than capability
arguments, then check that it survives being wrong about the supplier.**
The distinction is what makes a decision durable:

- **Ownership arguments** — what recurring cost the choice imposes per unit
  shipped, what compounding asset it starves, what it does to the thing your
  strategy names as your advantage — hold no matter how good the supplier turns
  out to be.
- **Capability arguments** — *"they can't do this part"* — invert the moment the
  supplier improves, or the moment your read of them proves wrong. And your read
  is usually a desk read of their own marketing: in the origin case the
  supplier's product documentation was literally unreachable from the working
  environment, so the capability picture came entirely from press releases.

Label each argument as one or the other while writing. A recommendation built
on capability has a shelf life measured in the supplier's release cadence.

## Why
The failure this prevents is not choosing wrongly between two known
options — it is answering a question whose premise (that the thing is one
thing) was never checked, and then defending the answer with the most available
evidence, which is whatever the supplier says about themselves.

## Story

## Install
Write the decomposition as a table with one verdict per part
before writing any prose. State, next to each argument, whether it is about
ownership or capability. Then name the **revisit triggers** that would reverse
the decision, and make the cheapest one *a question to ask* rather than an
assumption to hold — a decision resting on an unpriced assumption about someone
else's pricing is one conversation away from being confirmed or overturned, and
leaving that conversation unhad is a choice, not a limitation.

**Related.** Practice 28 (frame from the audience's question) is the adjacent
move at the artifact level; this one operates on the decision itself, and the
two compose — the audience's question is often posed at the wrong granularity
too. Practice 25's adversarial pass will confirm every claim in a
wrongly-decomposed analysis, so the decomposition has to be challenged
separately.
