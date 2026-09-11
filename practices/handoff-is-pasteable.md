---
slug:        handoff-is-pasteable
title:       A handoff to another session is a repo name, a paste block, and a way back
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "asking the person to do something in another session"
index_clause: "name the repo, give the exact text to paste, end with the way back"
gates:       ["reply"]
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-10"
approved_by: "Morgan"
strength:    decided
source_practice_number: null
---
## Rule
When work has to happen in a session other than this one, the reply hands
over **three things, always, in this order**:

1. **Which repository to open the session in**, by name. Not "the other
   repo", not "your practice set" — the name the person types or clicks.
2. **The exact text to paste**, as one block, ready to copy with nothing to
   fill in or edit. It has to stand alone: the other session cannot see this
   conversation.
3. **How to come back** — the message to paste *here* when it is done,
   written out the same way, saying either that it worked or what went
   wrong instead.

**The third one is the one that gets dropped, and it closes the loop.**
Without it, neither side knows what this session still needs to hear.

**When there is more than one destination, every block is keyed by its
repository name and by nothing else.** No ordinals, no "session #2", no
numbering that mirrors the order the person happened to paste things in
earlier. Their numbering and yours will not match, and the block itself
cannot say which one is right, because the session reading it has no view of
either.

## Detail
A handoff that describes the task in prose and leaves the person to compose
the prompt has moved the work, not delegated it.

Write the paste block for a reader with no context: name the branch, the
file, the command, the expected outcome. If the other session should report
a measurement back, say which numbers.

Keep the return message short — one line the person can paste without
editing, plus room for what actually happened. *"Done, pushed to
`<branch>`"* / *"Failed: <what it said>"* is enough shape.

If more than one thing has to happen over there, it is still one paste
block, not three replies.

**And a block for one repository never mentions another repository's
work.** Not as context, not as a courtesy summary. A session that is handed
someone else's items spends its turn proving the files do not exist —
grepping for a check it does not have, resolving a commit that is not in its
history — and reports back an inventory instead of doing anything. That is
the expensive failure, not the confusion: the misrouted block reads as a
plausible instruction, so a session obeys it until the filesystem refuses.

The mechanical form that survives this: one heading per destination, the
repository's full name in it, and the block under it self-contained. If two
blocks would share a paragraph, the paragraph belongs in both, written out
twice.

## Why
Sessions cannot see or message each other, so the person is the only
transport, and every hop through them is a hop where a task can be
paraphrased into something else. Prose instructions get retyped from
memory; a paste block does not.

This is the outbound half of
[findings-return-through-repo](findings-return-through-repo.md). That rule
says a finding travels by the repository rather than by the person; this one
says that when a person genuinely *is* the transport — because only they can
open a session somewhere else — the load they carry is a block of text and
not a task to reconstruct.

## Story
Asked for by Morgan on 2026-09-10, in his own words: instructions should
give *"the name of the repo* and the exact text to copy paste in*, and then
those instructions should always finish with, reminding me to return to the
original session with a message to copy-paste there confirming its success
or sharing other issues."*

The condition that keeps producing these handoffs is documented in this
repo's own gotchas: `add_repo` refuses a cross-owner attach — it did so
again in the session that wrote this rule, for this account's private
individual set — so work spanning two owners **has** to be split across
sessions, and a session rooted here simply cannot reach the other side.

**The multi-destination clause was added the same day, by the rule failing
on its first real use.** Three sessions were running, one per practice set.
Morgan had pasted their results back numbered #1, #2, #3; the reply answered
with three blocks numbered 1, 2, 3 whose repositories mapped to his #3, #2,
#1. Each block did name its repository correctly — the rule above was
followed — and each also carried a "(session #N)" cross-reference pointing
the other way. The block written for `precedent-individual` went to the
`precedent-team-repo-maintenance` session, which spent its turn establishing that
`check_commit_author.py`, `TODO.md` item 1, PR #60 and commit `8e0fc68` were
all absent, and answering: *"everything naming 'your work' belongs to another
session."* It was right. The repository name was in the heading and the
ordinal beat it, because an ordinal looks like an address and a heading looks
like a title.

## Install
Nothing to configure. It fires when a reply asks the person to go elsewhere.
