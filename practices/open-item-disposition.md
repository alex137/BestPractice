---
slug:        open-item-disposition
title:       An open item carries a disposition, and silence is the default
tier:        on-demand
severity:    default
applies_to:  ["**/TODO.md", "templates/TODO.md.template"]
occasion:    "writing or triaging an open item, or deciding whether to raise one in a reply"
gates:       ["reply"]
index_clause: "an item is raised in chat only if it says `ask`; absent means stay quiet"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08"
---
## Rule
Every open item carries a **disposition** — whether a session may raise it
with the owner. `parked`: recorded, and no session brings it up unprompted.
`wait`: blocked on someone, and nobody chases them. `ask`: a session may
raise it. **An item with no disposition is `wait`**, and only the person an
item waits on may set it to `ask`.

## Detail
The disposition is a line of its own inside the item:

```
**Disposition:** parked (2026-09-08, Morgan)
```

The value is one of the three words. The date and the name are mandatory on
`parked` and `ask` — a disposition nobody owns is the same silence this
replaces. A `wait` item normally carries no line at all, since absence
already means `wait`; write it out only where a reader would otherwise
wonder whether it was forgotten.

**Parked is not closed.** The item keeps its anchor, its text, and its place
in the list. A session may still read it, act on its content, and finish it
when the owner asks. What parking governs is one thing only: surfacing the
item to the person who parked it. Removing or changing a disposition is the
owner's call, never a session's — including "this seems important now."

An `ask` item is a standing invitation, not a queue to drain. It is raised
when it blocks the work in the thread, in the words the item already
carries.

## Why
Capture and salience were travelling on one channel. A repository that
records everything — the habit that makes it the memory — had no way to say
*recorded, now stop mentioning it*, so every session read every open item in
the same voice and the price of writing something down became the price of
being asked about it forever. That is a tax on the exact discipline the
repository is built on, and people pay it by writing less down.

The pump is a good rule with a side effect. [todo-is-a-handoff](todo-is-a-handoff.md) requires a
queued item to state a blocked-on input and, for a decision, **name its
owner**. That is right, and it converts every undecided minor thing into
"blocked on <person>" — which the next session reads as a standing
instruction to go get the answer. Naming the owner should record who can
close an item, not authorize every session to chase them.

**Recurrence tracks contact frequency, not importance.** An undecided rule
that sits on the last action of every session is touched every session; an
undecided rule about deck rendering is touched when someone builds a deck.
Several parallel sessions each raising a small question once, correctly,
arrives at one person as one assistant nagging repeatedly — and no session
can see that from inside its own thread. Only the file can, which is why the
restraint has to live there.

The default is silence because the two errors cost differently. An item that
went unraised is still in the file, losing nothing but time. An item raised
needlessly spends attention that cannot be refunded, and spends it on the
person least able to ignore it.

## Story
Morgan, 2026-09-08, on a question that had come up repeatedly in a single
day across five parallel sessions — what a session should do when he has
*not* said "Go merge": *"it is suuuuuuuuch a tiny minor issue and I want to
focus on the bigger issues etc. So I get frustrated when you keep on
bringing it up."* On the capture habit itself, in the same message: *"I love
how the BestPractice is to put everything we discuss on the TODO (that is
amazing so we never forget anything), but some things are just minor and you
don't need to keep on bringing them up so insistently."*

[TODO.md](../TODO.md) held 52 open items at that point and nothing in the
format could distinguish one he wanted pressed from one he had already heard
and set aside. The question in question was genuinely undecided and
genuinely minor, and he had no pattern yet to turn into a rule — so every
session, arriving fresh, correctly found an open decision blocked on him and
correctly raised it.

## Install
Write the disposition line into the item itself, in the format above.
Nothing has to be backfilled: an item with no line is `wait`, which is the
quiet state.

The TODO template ([templates/TODO.md.template](../templates/TODO.md.template)) carries the convention in
its header, beside [todo-is-a-handoff](todo-is-a-handoff.md)'s. The `reply` gate carries this Rule, so
it is in front of a session at the moment the raising would happen —
`python3 tools/precedent_gate.py reply`. The grammar is enforced by
`python3 tools/precedent_check.py --only open-item-disposition`.
