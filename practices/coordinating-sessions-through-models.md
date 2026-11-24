---
slug:        coordinating-sessions-through-models
title:       A project worked by several sessions is coordinated through a registry and a build tool, never by hand
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Coordinating several sessions is a moment, not a file; the occasion index reaches it, under the occasion it shares with tasked-session-stays-reachable because the universal set's index allowance had 15 tokens left."
occasion:    "tasking a session with long work, changing its plan, or working for one"
gates:       []
index_clause: "several sessions: one registry, one build tool, computed figures"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-11-23"
approved_by: "Alex, 2026-11-23: 'Yes on both', to landing this practice on main and to the shared-openings thread; first relayed the same day as 'Yes update precedent'"
strength: assented
---
## Rule
**When several sessions work on one repository, what they share is written once, in a file a tool reads, and never carried in messages or kept in the coordinator's head.**

1. **A choice every worker depends on lives in one registry file every script reads** ([registry-source-of-truth](registry-source-of-truth.md)). A decision is a one-line change there. No message to a worker carries the value, and no script types it in.
2. **A quantity two notes need has one home.** The second note reads it from the first, or asserts that its own equals the first's ([scripts-assert-properties](scripts-assert-properties.md)).
3. **One quantity has one name.** A new entry is compared with every entry already there before it is added, and a check lists any two differently named entries that carry the same value and unit. Each pair listed is merged, or recorded as different with the reason.
4. **One committed command rebuilds everything, in an order it works out itself** from what each step reads and writes. The order is never kept by hand, and never in a scratch folder ([repo-is-memory](repo-is-memory.md)).
5. **A session takes another session's files as they are.** It never regenerates them on its own branch.
6. **A check for anything dropped runs before every push:** a figure, marker or block another script reads that this change removed.
7. **The coordinator reports only figures a script printed, and only settled ones.** Anything else is called "not yet computed". A headline names the unverified assumptions it rests on ([numbers-are-sourced](numbers-are-sourced.md)).

## Detail
**The registry is for choices, not results.** Which design leads, what it is measured against, which variant is the baseline: these are decisions the person makes and changes. Each script reads them and computes from them. A check flags any note that quotes a figure computed for a different choice than the registry now holds, so a changed decision shows up as a list of notes to rebuild, not as a round of messages.

**An assumption's evidence belongs to the design it was run on.** Each assumption a headline rests on is listed in the registry beside the design its evidence came from. When the design changes, that evidence is marked as an earlier design's until it is run again. Evidence gathered on one design and quoted for another looks exactly like evidence.

**Twins are caught when they are born, or not at all.** Two workers who each need the same quantity will each name it, differently, and both names then live on: every rule about one home is satisfied twice. On the day the second is added the two are still equal, and a comparison of value and unit finds them. Once one has been updated and the other has not, they differ, and no comparison of values will ever pair them again. So the check runs when an entry is added and before every push, each entry says in a line what it measures so a reader can match by meaning, and a pair found equal by coincidence is recorded as different so it is not raised twice. Where the build is cheap enough, a stronger test: change each choice in turn and rebuild; two entries that move together under every change are one quantity.

**The full check comes due when the registry changes, never on a clock.** The cheap comparison runs at every push. The full check, which is the reading by meaning and the change-each-choice test, is too slow for that, so the registry records when it last passed, and a change to any entry runs it again once that record is old enough: by age, or by how many entries have changed since, whichever comes first. Both limits are choices written in the registry. A project nobody is changing pays nothing, and one changing fast is checked often. The record is one line for the whole registry, written only by the check itself; a stamp on every entry would be rewritten by every session and collide at every merge.

**The build command learns its order.** It records what each step read and wrote on a real run and orders the steps from that. Where two steps feed each other, it reruns them until nothing changes, and stops with both named if they never settle. A step added later needs no entry in anybody's list.

**Why a session never regenerates another's files.** A branch that rebuilds a file its session does not own carries that file as of its own starting point. Merged, it resets the owner's later work without a conflict, because to git it is simply the newer change.

**Settled, not first.** A worker's first figure is often revised within the hour. A coordinator that passes each first figure on has the person reading a number that is already gone. Report what the build printed after the pieces were put together.

This sits beside [working-in-parallel](working-in-parallel.md), which is about people claiming work in a shared repository, and [tasked-session-stays-reachable](tasked-session-stays-reachable.md), which is about whether a change of plan arrives. This rule makes most changes of plan a registry edit instead of a message.

## Why
Each worker's own work can be a sound model while everything between the workers is done by hand. Then the project's weakest parts are exactly the ones nobody modelled: which choice is current, what order things rebuild in, whose file is whose, and which figure the person was told. Those fail quietly, and they fail every time a decision changes.

## Story
2026-11-23, in a project run by one coordinating session and more than fifteen workers. Every worker kept a note and a script that printed and checked its own figures. The design's choices were changed several times in one day, each time by a message to every worker, and each worker re-pointed its own script by hand. The rebuild order lived in a script in the coordinator's scratch folder. Several landings in a row failed: on rebuild order, on a dropped marker, on a branch that reset other workers' files. The coordinator's reports carried arithmetic done in the chat when a worker's figure was not ready. The person asked whether the work was being done by inference where it should have been a model. The project then built the registry, the build command and the dropped-marker check; the check caught a removed figure another script read before it reached the trunk. Later the same day an assumption turned out to rest on evidence run on a different design than the one being built, which is where the rule about evidence comes from.

## Install
Nothing to install from here. The registry file, the build command and the dropped-marker check are the project's own, written for what it builds. A coordinating session loads this rule when it starts tasking workers, and says in each worker's brief where the registry is and that no message will carry a choice.
