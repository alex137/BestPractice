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
When the person says **"Vocabulary"**, list the standing commands in force
here -- each phrase, and one plain sentence saying what it does -- and
nothing else. No preamble, no closing offer, and no advice about which to
use.

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

## Detail
**The field is the registry** (practice:
[registry-source-of-truth](registry-source-of-truth.md)). A command practice
declares its own phrases in frontmatter:

```
command:     {"Go merge": "Save the work, publish it, and tell you where it went."}
```

an object mapping each trigger phrase to the plain sentence a person who is
not a developer reads ([readers-vocabulary](readers-vocabulary.md) governs
that sentence -- it is written for them, not for a session). Two phrases for
one command are two entries in one object, never two practices: `Go merge`
and `Approved` are one rule with two triggers.

**Alphabetical, always.** Every other order -- by date coined, by how often
it is used, by how important someone thinks it is -- is a judgment that goes
stale and that the person asking cannot predict. A lookup is sorted.

**Adding a command is one edit.** Write the practice, give it a `command:`
field, and it appears in this answer, in the reader-facing table, and in
this repository's own generated views without anyone updating a list.
Editing any of those rendered copies by hand instead is
[generated-edit-goes-upstream](generated-edit-goes-upstream.md)'s failure.

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
[the day-to-day document](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/documentation/HOW_TO_USE_THIS_DAY_TO_DAY.md)
had ten of the eleven, missing the practice check, and the prose in the
project instructions ran to several paragraphs per command. The table is
generated from the practice files now.

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
