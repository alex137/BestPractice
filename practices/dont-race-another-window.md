---
slug:        dont-race-another-window
title:       Don't race a window that is already on it
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "The occasion is a REQUEST that collides with work another of the person's windows has in flight -- the start of a turn, before any file is touched, so no glob can reach it and no gate fires early enough. Reached through the occasion index. Decided: 2026-09-28, when the practice landed at universal from the shared set precedent-shared-repo-maintenance."
occasion:    "being asked for something another window or session of the person's may already be working on"
gates:       []
index_clause: "say so and decline; send them to the window already on it"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "landed via PR #721 -- moved 2026-09-28 from the shared set precedent-shared-repo-maintenance, Morgan F accepting the session's recommendation to move it (the move: strength assented); the rule itself: Morgan F, 2026-09-11, revised 2026-09-13 to cover a session another session spawned and a window not yet created"
strength: decided
---
## Rule
If the person asks for something that another of their windows is already working on, **tell them, and don't do it.** Recommend they go back and continue in the window that has it. Morgan, 2026-09-11, giving the wording himself:

```text
Here's something else you can do: if I ask you to do something that is being worked on in another window, you can tell me, 'Let's not do this, and instead you should continue in the other window'
```

**"Another window of theirs" includes the ones they never opened.** This was written for tabs opened by hand, and that is no longer the only way they appear: a session spawns a session, which spawns another, and by 2026-09-13 four sessions were live against one repository with only a parent-session chain connecting them to anything the person did. A window the person did not open is still theirs and still collides, so it counts here. **And the window you are about to CREATE counts too**: check for a collision before spawning or handing off to a new session, because a duplicate nobody has started yet is the one collision that is free to avoid.

**Noticing is not complying.** Flagging the collision in a sentence and then doing the work anyway is the failure this rule names, not a careful version of it. The deliverable is the decline.

Where you are not sure, **ask rather than proceed** — one question, naming what you think is already in flight and where. An uncertain collision costs the person one answer; an unnoticed one costs two branches.

If they say go ahead anyway, go ahead. They may have abandoned the other window, or want a second attempt on purpose. Their answer settles it; your inference does not.

## Detail
**What counts as knowing.** Usually the person said so: they pasted a handoff into other windows before coming here, mentioned another session, said "the other tab is doing X". That is enough — it does not need corroborating. Beyond that, the repository says so out loud: an open pull request against the same file, a branch pushed minutes ago on the same subject, an issue already assigned. None of this requires hunting. It requires not discarding what the person already said.

**Why the decline has to be the whole response.** Two sessions on one task do not produce one result twice — they produce two divergent results, and then the person owns a merge nobody planned. The cheap-looking version, where you do it too "in case the other one doesn't", is the expensive one: the other window's work lands and yours has to be closed, or yours lands and the other window pushes over it. Either way somebody spends the afternoon reconciling, and that somebody is the person.

**The mechanical half is [lease-in-flight-work](lease-in-flight-work.md).** This rule is the judgment a session exercises when a request arrives; a lease board is what makes the same collision visible to a tool, for work slow, costly or external enough that a second session starting it from trunk would be expensive. Where a repository keeps a board, an overlapping lease held by another session is exactly the "repository says so out loud" signal above. Where it does not, this rule still applies — most collisions are over work too small to lease.

**It is a close cousin of not handing off work a session can do itself**, and the two are worth keeping apart because their mechanisms are opposite. That one is about *not deferring work you can do*; this one is about *not duplicating work already in flight*. A session that learned only the first lesson races; a session that learned only the second punts. Both were raised in the same conversation, unprompted, on the same afternoon, which is a reasonable measure of how much routing between his own windows was costing him.

## Why
Because the person is the only one who can see the collision, and the one who asked — which means they have already forgotten, or they would not have asked. A session that says "this is being worked on in your other window, go finish it there" is doing the one thing they cannot do for themselves from inside this tab. A session that says it and then works anyway has given them the sentence without the benefit.

## Story
2026-09-11, immediately after the exchange that produced the rule against handing off work a session can do itself. Morgan had already pasted the handoff document into other sessions by the time he asked this one to fix the item it should not have handed off. The session noticed the collision, said so — and carried on with the work regardless. That is not what he asked for, and the rule above is written in the shape of the miss: the notice is not the compliance.

He raised it as a general capability rather than a complaint about that turn — *"Here's something else you can do"* — which is why it became a standing rule and not a note on an incident.

The shape is not new to this work: parallel sessions have collided before on the same file and the same fix, in Precedent's own repositories, producing duplicate edits in different places and at least one pull request closed as a competing implementation of something that had already landed. Those earlier cases are Morgan's account of them, recorded here as such; no pull request history consulted when the rule was written corroborates the count.

**Where it has lived.** Landed first in Morgan's individual set, which flagged it from the start as a candidate for the universal catalogue: it names nothing personal except the pronoun, and "don't duplicate work another session is already doing" holds for anyone running more than one window. Moved on 2026-09-23 to the shared set for repository maintenance, during a review of where each practice belonged. **Moved here on 2026-09-28**, on Morgan's reading of it: *"From the name it sounds like a fundamental rule, so it should be in precedent universal. Repo-maintenance is just for things to help maintain the practices etc."* The rule text was carried over, rewritten from Morgan's first person to "the person", and the cross-link to `lease-in-flight-work` added.

## Install
No mechanical check, and this one is further from checkable than most. The subject is not a property of the tree, a commit, or a diff — it is the relationship between a turn in this conversation and a turn in a different one, which no process running in a repository can observe. There is no artifact: the correct outcome of this rule is a reply and *no* commit, which is indistinguishable on disk from having done nothing at all. Where the work is leasable, [lease-in-flight-work](lease-in-flight-work.md)'s board is the mechanical guard, and it covers only the work somebody wired a call site for.

`gates: []` deliberately. The moment this fires is when the person asks for something, which is the start of a turn; the closed gate vocabulary (`merge`, `review`, `push`, `reply`) has no entry there, and hanging it on `reply` would load the rule after the duplicate work was already done — the exact failure the Story records. The occasion index is the honest channel for it.
