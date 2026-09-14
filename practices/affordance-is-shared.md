---
slug:        affordance-is-shared
title:       An affordance you build for yourself is an affordance you hand to everyone
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "building a mechanism that makes something discoverable or reachable"
gates:       []
index_clause: "name who else the mechanism you just built now serves"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 43
---
## Rule
**The practice.** When you add a mechanism so that *your* system can do something
— find a thing, reach a thing, identify a thing — write down who else that
mechanism now serves, before you call the design done. The question is not
"could this be abused" in the abstract; it is the concrete one: **the capability
I just built is available to whoever else shows up, so who shows up?**

## Detail
**What to do instead — three moves, in order of how much they usually buy:**

1. **Invert the default from announce to answer.** The strongest fix is usually
   not to protect the broadcast but to *stop broadcasting*: have the thing stay
   quiet and respond only to a request that proves who is asking. This changes
   the exposure from *proportional to time* to *proportional to authorized
   demand*, which is a different order of problem, and it is frequently cheaper
   than the thing it replaces.
2. **Split channels by who they serve, not by convenience.** One channel doing
   two jobs leaks the audience of the first to the audience of the second.
   Separate the local, operational path from the wide-area, custodial one, and
   each stops advertising the other's business.
3. **Make the exposed state a setting, not a property.** Where the exposure is
   genuinely required *sometimes* — a safety obligation, an interoperability
   requirement, a regulator's rule — do not resolve the conflict once at design
   time. Make it a state chosen per deployment by whoever knows the local
   conditions, and revocable afterwards, because the thing itself is usually in
   no position to judge.

**Two things worth checking while you are there.** First, **name the threat set
rather than saying "secure"** — the honest claim is almost always tiered
("undiscoverable by anyone with a commodity receiver; not by a well-equipped
state"), and a single unqualified word is the tell that nobody enumerated. Say
which tier you mean to each audience, and do not carry the generous phrasing into
the room where the demanding one applies. Second, **run the cost arithmetic
before assuming the safe option is the expensive one.** The intuition that
discretion is a premium feature is often simply false — and if it is false in
your system, that is a strong argument for making the discreet posture the
default rather than the upsell.

## Why
**Why it needs a rule.** The mechanism is added under a benign framing —
*"it needs to report where it is, so we can come back for it"* — and inside that
framing nothing looks wrong. The design review then checks whether the mechanism
works, which it does. Nobody is prompted to ask what the mechanism does for a
party who was not in the room, because the requirement that motivated it never
mentioned one. So the gap is not carelessness; it is that the framing of the
requirement is also the framing of the review.

**The tell:** a mechanism whose whole job is to *make something discoverable*, or
*reachable*, or *distinguishable*, where the thing is left alone, is valuable,
and the discovery channel is open to anyone. Locators, published identifiers,
default-on telemetry, convenience access paths, health endpoints, indexes built
so *you* can find your own assets — all of them work exactly as well for someone
else.

## Story

## Install
**Related:** [verify-decomposition](verify-decomposition.md)(a) — compute the term whose direction is the point,
rather than reasoning about which way it goes; here the term is the cost of the
cautious option, and the reasoning was backwards.
