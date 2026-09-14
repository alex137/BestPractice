---
slug:        checks-carry-a-declared-decline
title:       A check a repo cannot legitimately clear carries a declared decline
tier:        on-demand
severity:    default
applies_to:  ["tools/**/*.py", "practices/**"]
occasion:    "writing or changing a check that can report a deliberate state"
gates:       ["review"]
index_clause: "a check reporting a state a repo chose needs a declared decline, with a reason"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "Morgan, 2026-09-14 (decided)"
---
## Rule
**When a check reports a state a repository can legitimately be in on
purpose, it carries a way to DECLARE that on purpose** — and the
declaration carries a **reason**.

The reason is the whole thing separating a decision from a silenced check.
A bare opt-out list is a mute button; an opt-out with a reason is something
the next reader can disagree with, which is what an exemption is for.

**The test is whether a correct repository can reach a clear state.** If
the only way to stop the check reporting is to change something the repo
decided against, the check has no clear state available to it and will be
ignored — and a check people have learned to skip costs more than it was
ever worth, because it stops being read on the day it is right.

**Declare the failure modes too, rather than accepting a declaration
blindly.** Three come with every exemption list and each means the
declaration has come loose from the tree: an entry with **no reason**, an
entry naming something **not present**, and an entry that **contradicts
what the repo does**. Report all three. An exemption that outlives what it
exempted is a standing hole nobody can see.

## Why
A check earns its place by being read, and the thing that stops it being read
is not noise in general — it is a repository that **cannot win**. Noise you
can clean up. A finding with no legitimate clear state is permanent, and the
person learns the fastest thing available: skip this one. From then on the
check is dead weight that still costs a run, and it is dead on the day it is
finally right about something.

The asymmetry is what makes the escape hatch cheap. Writing one costs a list
and a reason field; not writing one costs the check's credibility across
every repository that adopts it, and nobody is watching for that failure
because a check nobody reads reports nothing.

**A reason field, specifically, is what keeps this from being a mute
button.** An exemption list with no reasons is indistinguishable from
suppression, and the thing a reviewer needs is not the fact that somebody
opted out — it is the argument they opted out on, so they can say it is
wrong.

## Story
`hooks-on-disk-are-reachable` reported every harness adapter a consuming
repo had deliberately left unwired. The mechanism that writes adapters in
refuses to edit a consumer's `settings.json`, by design — copying that
would silently repoint the consumer's base branch — so a repo that did not
want a particular adapter could never reach a clear state. The only way to
silence the check was to wire a hook the repo had decided against.

The decision existed and was written down. A real consuming repo recorded
in its own instructions file that it declined the freshness guard because
its bootstrap already fetches and fast-forwards. That is exactly the reasoning
an exemption should carry, and the check could not read it: prose is
deliberately not searched, since a document mentioning a filename is not an
invocation.

Fixed 2026-09-14 by adding `declined_adapters` to `precedent.json` — the
reason satisfies the check, never the wiring — with the three broken states
above each reported. Raised as a universal candidate the same day and
approved by Morgan, who had asked for exactly this before the wider
adapter rollout rather than after it.

## Install
No check exists for this practice itself, and it is not obvious one can:
whether a given check reports a state a repository can legitimately choose
is a judgment about that check's subject matter, not a property of its
source. It fires at the `review` gate instead —
[tools/precedent_gate.py](../tools/precedent_gate.py) review — so a session
writing or changing a check is handed this Rule at the moment it matters.

The worked example is in this repository and is the shape to copy:
`declined_adapters` in [precedent.json](../precedent.json), read by
`hooks-on-disk-are-reachable` in
[tools/precedent_check.py](../tools/precedent_check.py), with its four
planted cases in [tools/verify_harness.py](../tools/verify_harness.py) —
the declared decline passing, and each of the three loose-declaration
states firing.

An adopting repository installs nothing: the practice reaches every session
through the generated occasion index.
