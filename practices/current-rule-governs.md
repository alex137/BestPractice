---
slug:        current-rule-governs
title:       A command means what the rule in force says now; history is for investigating, never for deciding whether to do it
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "a person gives a standing command, or asks for something a practice already governs"
gates:       []
index_clause: "do what the rule in force says; old copies and deferrals are history; never decline silently"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-24"
approved_by: "Morgan, 2026-09-24 -- asked for a root-cause fix after a session
  answered \"Go update\" with a question, having reasoned from a stale copy of
  the rule: \"those are the time and places to review the whole history, not
  when I say 'Go do X'\""
strength:    decided
---
## Rule
**A standing command means what the rule in force says today, and you do
it.** Resolve the command to its active practice
(`precedent_show.py SLUG` follows a deduplicated copy to the live one) and
carry it out. **Superseded, deduplicated and retired entries, `## Story`
sections, old deferrals and past decisions are history.** Read them to
investigate a failure, or to back a proposal to reconsider a rule. Never
read them to decide whether to do what was just asked.

**Do it first, and propose reconsidering after**, in the same reply if you
want to. **Never decline silently:** if you are not doing what was asked,
the first line of the reply says so, and why.

## Detail
**Finding the rule in force.** Through the loader this is already done for
you: the occasion index lists every command, and
[tools/precedent_show.py](../tools/precedent_show.py) prints a
`NOT IN FORCE HERE` banner on a redundant copy and names the slug to load
instead. Reading a practice file by hand, look at its `status:` before its
`## Rule`. Only `active` is a rule. `deduplicated` names where the rule
lives now in `in_force_at:`. A successor lists what it replaced in
`supersedes:`.

**Copies count as copies wherever they sit.** A paragraph in an installed
`AGENTS.md`, a note from an earlier sync, a summary in a handoff prompt and
a practice in someone's own set are all copies of a rule. When a copy and
the rule in force disagree, the rule in force wins, and the reply says
which copy was stale so somebody can fix it. **A hand-written rule that
covers something no practice covers is not a copy.** It is that
repository's own rule, and so is a local exception the person has
confirmed on purpose.

**Between layers, the newer decision by the same person beats that
person's older copy.** Source precedence (team, then repo-local, then
individual, then universal) ranks rules that are *both current*. It exists
so that a team can outrank the world, not so that a copy someone forgot to
update can outrank what that same person decided later. A clause like
"the personal pack wins on conflict" works the same way. So where two
live copies of one person's decision disagree, do what the newer one says,
name the older one in the reply, and mark it `deduplicated` or bring it
up to date in the same change.

**A deferral covers the text it was made against, and nothing newer.**
"Declined as a duplicate" or "deferred" at one sync says nothing about a
practice that changed after it. At the next sync the decision is made
again against the current file
([vendor-update-runbook](vendor-update-runbook.md), step 4), and
[tools/practice_audit.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/practice_audit.py) fails on a recorded
decline whose upstream file has changed since.

**Reconsidering is always open. It just comes after the work.** *"I know
`Go update` is in effect, but maybe we should reconsider it"* can be said
at any time. How hard to argue depends on the approval's `strength:`
([decision-strength](decision-strength.md)): an `assented` rule can be
argued freely, and a `decided` one gets an open item rather than a debate
in the thread. Neither one is a reason to leave the command undone.

**What legitimately stops a command.** A step that was actually refused
(quote the refusal), a check that is red, or a sentence that really could go
either way ([go-merge](go-merge.md) says how to say that out loud). An
older rule that said something else is not on that list. Neither is a
feeling that the person might not have meant it.

**A relayed summary of the rules is a copy too.** A prompt handed over
from another session describes the rules as that session understood
them. Before acting, check each command it names against the practice
files. The relay that asked for this practice listed `Session Text` among
the standing commands, and that practice had already been folded into
[prompt-please](prompt-please.md) on 2026-09-20.

## Why
Morgan, 2026-09-24, on the incident below: *"I love having the history, and
that's a key part of bestpractice/precedent BUT that's for investigative
purposes, that's to help debugging when we're trying lots to know what was
tried, that's also for when you specifically make a proposal to reconsider
a rule ... but those are the time and places to review the whole history,
not when I say 'Go do X'... relitigating every single decided issue instead
of doing it, but worse the relitigating is you just NOT doing it for no
reason and not even telling me, it's not a way we can work in."*

This repository keeps its history on purpose. Superseded practices keep
their files, Story sections record what was tried, and deferrals are
written down. All of that is good for debugging. It becomes a trap when a
session treats it as the rule. The history is always bigger than the
current rule and usually more cautious, so a session reading all of it
will always find some reason to hesitate. Two costs follow. The work does
not get done, and the person may not find out that it didn't, because the
hesitation shows up as a question or as nothing at all.

Putting the silent case first is deliberate. A session that does the thing
and argues against it afterwards has cost one paragraph. One that
quietly does something else leaves the person thinking the work is done.

## Story
**2026-09-24, in a dependent repository installed the classic way.** The
person said `Go update`. The session did not treat it as authorization. It
asked instead, and told him that only a standalone final "go", "merge" or
"PR & merge" counted. That is the three-trigger rule the person's own
set had itself replaced on 2026-09-04. The universal practice took over
on 2026-09-08 and has been loosened several times since.

The stale reading got in through three gaps, and each is closed somewhere:

1. **A deferral that was never revisited.** The repo's 2026-08-29 sync
   declined upstream's merge-keyword practice as a "duplicate" of the
   person's own rule. Two later syncs re-applied the installed layer
   without looking at that decision again, and upstream's rule changed
   underneath it. Closed by step 4 of
   [vendor-update-runbook](vendor-update-runbook.md) and check 6 of
   [tools/practice_audit.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/practice_audit.py).
2. **A precedence clause that ranked an old copy above a newer decision.**
   The installed instructions said the personal pack wins on conflict, and
   the personal copy was the older one. Closed by this practice's
   between-layers paragraph.
3. **No loader, so no command list.** A classic install never gets the
   occasion index, so none of the standing commands reach it. That install
   path was retired on 2026-09-23 and such repos now migrate
   ([spec/MIGRATING_EXISTING_INSTALLS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/MIGRATING_EXISTING_INSTALLS.md)).
   After migrating, the index lists every command and this practice
   arrives in the resident block.

None of those gaps would have mattered if the session had done what the
current rule said and then raised the conflict. That is the rule this
practice adds.

## Install
Resident, so every repository running the loader carries it in its
generated instructions block. Nobody has to copy it into hand-written
prose. **The judgment itself cannot be checked mechanically.** A transcript
where a session asked a question looks the same as one where the question
was fair. Two of the ways in are checked, though: `precedent_show.py`
redirects a deduplicated slug, and `practice_audit.py` check 6 fails on a
decline that the upstream file has moved past.

**Related:** [go-merge](go-merge.md) (the command this was coined over),
[decision-strength](decision-strength.md) (how hard a reconsideration may
push), [docs-are-current-state](docs-are-current-state.md) (a document
states what is true now) and
[index-remembers-past](index-remembers-past.md) (lineage lives in the
index, not in the rule a session acts on).
