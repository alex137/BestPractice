---
slug:        show-what-you-point-at
title:       Everything a reply points at is in the reply, or linked
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A reply is not a file, so no glob names the moment it is written; reached by the `reply` gate instead, like fence-block-for-paste. Decided: 2026-11-20."
occasion:    ""
gates:       ["reply"]
gates_why:   "Its occasion is every reply. The stop hook refuses a reply that breaks it whether or not the session thought of it, so an index line would add nothing."
index_clause: "what a reply points at is shown in it or linked, never just named"
index_required: false
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-11-20"
approved_by: "Morgan, 2026-11-20 (strength: decided), after a reply asked him to decide on \"Five new rule and process candidates from last night\" and never listed the five: \"how do we solve the general problem that you keep on referencing things that I have no idea what you're referencing since you don't put it there or link it (sometimes its in docs linked, sometimes it's mentioned dozens of messages from hours earlier etc).\" He chose BestPractice as its home over the ladder and writing sets the same day. Raised before on 2026-10-29, when about eight replies running asked him to answer \"the voice pack question\" without saying what it was."
strength:    decided
source_practice_number: null
---
## Rule
**Everything a reply points at is in that reply, at least one line each, or
linked straight from the line that points at it.** That covers a question,
a list of items, a candidate, an option, a section of a document, and
anything said earlier in the conversation. The person may read only this
reply, hours later. Scrolling back through the thread is exactly what fails.

**Never one of these on its own:** "question 1", "the five candidates",
"as above", "as discussed", "the X question", "the items above", "item 6".
Each is a name for something, not the thing. Write the thing itself: the five
candidates as five lines, question 2 as the question, the earlier point as
one sentence. Or link it, when it lives in a file, a pull request or a page.

**This holds for the whole reply**, not only The Boildown's Your next steps.

**A list shown somewhere else in the same reply counts as shown.** "Keep
all five" under a list of the five, earlier in the reply or as sub-bullets of
that line, is fine. So is an inline listing ("three options: merge now, wait,
or drop it") and a link on the line.

**Enforced by the reply gate** (`require_references_shown` in Precedent's
`reply_check.json`, id `boildown-references-shown`). It refuses a reply that
names a counted set of two to twelve things ("five candidates", "the three
rules") with no list of that many elsewhere in the reply, an inline listing
or a link; a numbered item ("question 2", "option B") the reply never
shows; a named question the reply never asks; and a pointer into the
thread ("as discussed", "mentioned earlier", "from last night") or within
the reply ("the items above") with nothing there to point at. Fenced blocks,
blockquotes, code spans and double-quoted citations are not read, so a
reply can quote the phrases this rule forbids.

## Detail
**What counts as a list.** Bullets or numbered lines at one indent under one
parent, or a table's rows. The list the pointing line itself sits in does
not count, so a Boildown with five bullets does not show "five candidates"
named in one of them. Sub-bullets under that line do.

**What the check does not read.** Counts larger than twelve, which are
statistics ("81 findings") rather than a set the reader is asked to look
at; counts that are part of a date or a version; a singular noun after a
count ("the three private practice sets" names sets); a count of the form
"N of M", which the Boildown's first line uses for work not yet landed. A kind of question ("the full
question", "the reader's question") is not read as a pointer to one.

**When the check is wrong.** It reads patterns, not meaning, so it can
refuse a reply that really does show what it points at in a shape it does
not know. The fix is to show it plainly as a list or link it, not to reword
around the check ([upstream-fix](upstream-fix.md)); if the shape is common,
teach the check, in [precedent_reply_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_reply_check.py)'s
`unshown_references()`.

## Why
A name for a thing is not the thing. "The five candidates" means something
to the session that just wrote them down and nothing to a person reading
one reply after hours away. The question check that came before this one
made each ask carry its stakes and a pick, and a reply still passed it
while pointing at five things it never showed. The cheapest place to fix
that is the reply itself, in the turn it is written: one line per item, or
one link.

## Story
2026-11-20: a reply's Your next steps said "Five new rule and process
candidates from last night: keep marks each in force... My pick is keep all
five" and never listed the five. It passed the reply gate, because
`require_ask_states_its_question` checks that an ask gives its stakes and a
pick, not that the things it points at are shown. The Boildown's item 1
already said "no reference that needs the thread open", but only for Your
next steps, and nothing enforced it. Morgan asked for the general fix.

## Install
Nothing to configure. The reply gate carries it: registered on `reply`, it
is printed at the start of every turn, and the stop hook refuses a reply
that breaks it. The predicate is generic, so a practice set can declare its
own `require_references_shown` entry with its own nouns and pointers.
