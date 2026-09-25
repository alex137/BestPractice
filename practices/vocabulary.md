---
slug:        vocabulary
title:       "\"Vocabulary\" lists every standing command, read off the practices"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Vocabulary\", or asks what the standing commands are"
gates:       ["reply"]
index_clause: "\"Vocabulary\" -- list every command in force, read it, never recall it"
checked_by:  null
defines:     ["Vocabulary"]
command:     {"Vocabulary": "List every standing phrase this project recognizes, and what each one does."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-13"
approved_by: "Morgan, 2026-09-13 -- coined and placed at universal in the same message"
strength:    decided
source_practice_number: null
---
## Rule
When the person says **"Vocabulary"**, begin the answer with one line making
clear that these are not exact-keyword triggers: a session recognizes the
phrase, but it also reads plain language for the same intent and triggers on
that, the way [go-merge](go-merge.md) itself is read (*"sold, ship it"* counts
as much as the phrase does). Then list the standing commands in force here --
each phrase, and one plain sentence saying what it does -- and nothing else
beyond that opening line. No further preamble, no closing offer, and no
advice about which to use.

**Read the list, never recall it.** Run
`python3 tools/precedent_vocabulary.py`, which collects every practice
declaring a `command:` field across every source this session resolved, and
answer from its output. A list assembled from what a session happens to
remember is the failure this exists to prevent: the commands change, and
the one most likely to be missing is the one added most recently.

**Say which sources did not resolve.** The tool prints a note for every
source it could not read. That note goes into the answer -- *"I could not
read your team set, so any command it defines is not below"* -- because a
short list and an incomplete list look identical.

**A command a session cannot honour is not listed.** If a phrase's practice
did not resolve this session, it is not in the vocabulary this session has;
say what is in force, not what exists somewhere.

**"Nothing else" governs the BODY, not whatever closing section the reply
gate requires.** Where a source in force mandates a closing block on every
reply, that block still appears -- a rule this answer cannot satisfy is not
thereby suspended, and a stop hook will refuse the turn without it. What
"nothing else" forbids is the material a session adds *of its own accord*:
a preamble, an offer to go deeper, advice about which command to use, and
above all **an unsolicited diagnosis of something the session noticed while
assembling the list.**

**The unresolved-source note is the one thing that is NOT an aside.** Saying
which sources did not resolve is required above. Saying what you think went
wrong with them is not, and it is where this answer goes astray: the note is
a fact about the list's completeness, and any theory about its cause is a
separate investigation the person did not ask for
([diagnosis-is-measured](diagnosis-is-measured.md) governs that theory if it
is ever offered).

## Detail
**The field is the registry** (practice:
[registry-source-of-truth](registry-source-of-truth.md)). A command practice
declares its own phrases in frontmatter:

```
command:     {"Go update": "Save the work, publish it, and tell you where it went."}
```

an object mapping each trigger phrase to the plain sentence a person who is
not a developer reads ([readers-vocabulary](readers-vocabulary.md) governs
that sentence -- it is written for them, not for a session). Two phrases for
one command are two entries in one object, never two practices: `Go update`
and `Approved` are one rule with two triggers.

**Alphabetical, always.** Every other order -- by date coined, by how often
it is used, by how important someone thinks it is -- is a judgment that goes
stale and that the person asking cannot predict. A lookup is sorted.

**Adding a command is one edit.** Write the practice, give it a `command:`
field, and it appears in this answer, in the reader-facing table, and in
this repository's own generated views without anyone updating a list.
Editing any of those rendered copies by hand instead is
[generated-edit-goes-upstream](generated-edit-goes-upstream.md)'s failure.

**The printed count is SMALLER than the number of `command:` entries, and
that is correct.** It came up twice on 2026-09-21 as a suspected bug, from
two different sessions, so the arithmetic is written down here rather than
re-derived a third time. Measured on that date:

| | |
|---|---:|
| `command:` entries across all practice files | 23 |
| less entries in practices whose `status:` is not `active` | −3 |
| command names with an active practice behind them | **20** |
| less names collapsed as a SYNONYM onto another line | −2 |
| **lines the tool prints** | **18** |

The two synonyms are `Approved` (printed under `Go update`) and `Archive?`
(under `Archive`). The three inactive ones are `archive-command`,
`brief-it` and `session-text`, each `status: deduplicated` — folded into a
surviving practice, so their word still works and their entry is not a
second rule.

So a name appearing twice across the catalogue is the NORMAL shape of a
deduplication, not a collision: one claim is active, the other is not.
**Nothing currently stops two ACTIVE practices from claiming the same
word**, which would be a real ambiguity — a session would see two lines
with the same command and no way to tell which rule binds. There is no such
pair today; it is simply unguarded.

**Which is the whole reason this practice says to read the list rather than
recall it.** Both sessions that reported a discrepancy had counted
something reasonable — output lines, or frontmatter entries — and neither
number is the answer. The tool is the answer.

## Why
**The commands only work if the person knows them, and they were being asked
to keep the list in their head.** Precedent ships a growing set of standing
phrases, each saving a paragraph of explanation -- and every one of them is
worthless to someone who cannot remember what is available. A command that
prints the commands is the cheapest possible answer to that, and it is the
one part of the vocabulary nobody has to memorize.

**A hand-kept list of commands drifts on the day a command is added**, which
is the day it matters most. Before this, the list lived in two hand-written
places -- a paragraph of prose in the project instructions and a table in the
day-to-day document -- and both were updated by whoever remembered. Reading
it off the practice files removes the class: the definition and the listing
are the same fact.

## Story
**Coined by Morgan, 2026-09-13**, in the same message that added `Approved`
to [go-merge](go-merge.md) and pushed the merge authorization into spawned
sessions: *"maybe we can add in yet another vocabulary word: 'vocabulary' if
I type it, it then returns a list of the commands we have defined: go merge,
my options, spawn session, etc."*

The list he named in that sentence is itself the argument. It is three
commands and an "etc." from the person who coined all of them -- so the
version of this list held in anyone's head, his included, is already
incomplete. There were eleven phrases in force when he asked.

Two hand-maintained copies existed at that moment and neither was complete:
the reader-facing table in
[the day-to-day document](https://github.com/alex137/BestPractice/blob/staging/documentation/DAILY_HABITS.md)
had ten of the eleven, missing the practice check, and the prose in the
project instructions ran to several paragraphs per command. The table is
generated from the practice files now.

**First violated the day after it was written, 2026-09-14**, by a session
answering this exact command. Three team sources had not finished cloning, so
the tool printed its unresolved-source note correctly -- and the session then
appended a theory about *why* they had not resolved, plus a recommendation to
check whether the repositories still existed and delete their declarations if
not. Both named causes were wrong (the clone simply had not run yet), and
none of it had been asked for. The listing itself was correct and complete;
everything that went wrong was in the part this rule already said not to
write. That is what sharpened "nothing else" into the clause above, and what
[diagnosis-is-measured](diagnosis-is-measured.md) was written out of.

## Install
The tool ships with the engine as `tools/precedent_vocabulary.py`, and
adopters need nothing beyond it: the `command:` fields travel with the
practice files themselves.

No check on the ANSWER -- like every other command here, whether a reply
obeyed the shape lives in the conversation, where no repo-scoped script can
see it. What is checked is the part that used to drift: the reader-facing
table is a generated block registered in `tools/doc_sync.py`, so a command
added without that table being rebuilt fails
[computed-numbers-in-scripts](computed-numbers-in-scripts.md)'s gate. That
covers the copy; the phrases themselves have exactly one home.
