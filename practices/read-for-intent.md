---
slug:        read-for-intent
title:       Read a message for what it asks, never only for its words
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus. It governs how a message is read -- a person's, or one a session writes for another -- which no file path or gate moment reaches in time. Reached through the occasion index. Decided: 2026-10-08, when the practice landed at universal."
occasion:    "reading what a message asks for, or writing one that a session or a check will read"
gates:       []
index_clause: "the words, the context and the conversation; never the keyword alone"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-08"
approved_by: "Morgan, 2026-10-08 -- \"shouldn't it understand the intent behind commands not just the literal words? This is an important principle (maybe it should be a practice / principle, to always look for intent) and don't we already have a practice that does that?\"; the principle earlier in his words, 2026-09-28: \"don't just literally look at the words but think about the words I say, the context, what we had been discussing\"; Alex's intent-over-keyword point, relayed by Morgan, 2026-09-16"
strength:    decided
---
## Rule
**Read a message for what it is asking, from its words, its context and
what was just being discussed, never from a keyword alone.** A standing
command is recognized by what the message asks for: its phrase removes
doubt, it does not create a requirement. "Sold, ship it" is a go-ahead
with no command word in it, and "don't merge into main" is not one, though
it holds the words "merge into main".

**It applies to what you write for another session too.** A prompt that
says "make it live", "ship it" or `gh pr merge` grants a landing as
surely as one that says "merge into main", and is judged by what it grants.

**A check that matches words is a net, not the judge.** It catches the
likely cases and refers the rest to judgment. Its negations and exemptions
are read by meaning, clause by clause: a "no" governs the verb it sits
beside, so "Merge it into main, no questions asked" is still an order to
merge. Where a check cannot tell, it fails closed.

**Where a hard-to-reverse reading is a genuine judgment call, say the read
out loud and confirm first** (a push, a merge, a mark of how convinced the
person was). A full practice audit and a very deep check are kept to the literal
ask, because what they trigger is expensive.

## Detail
**Where the principle already bound sessions before it had a file.** Each
of these still holds and now points here rather than restating it:
[AGENTS.md](https://github.com/alex137/BestPractice/blob/staging/AGENTS.md)'s "Precedent commands" paragraph;
[vocabulary](vocabulary.md)'s opening line, which tells the person the
commands are not exact-keyword triggers; [weak-yes](weak-yes.md) and
[decision-strength](decision-strength.md), which read "sure, why not" for
`assented`; [archive-status-check](archive-status-check.md), whose phrase
came with its own "or other words to imply something like that"; and, in
the ladder set, `go-update`'s paragraph saying neither of its phrases is
required for the authorization to exist.
[spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md)
says the same of the stage words.

**How a check reads a negation.** In
[tools/precedent_reply_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_reply_check.py), a
`require_in_fence_paired_with` pair may carry
`negation_exempt_if_clause_negates`: a clause is forgiven only when a
negator sits in the few words before the landing verb ("do not open a PR
to main") or is its object right after it ("merge nothing into main"). A
negator after the destination, or in another clause, is about something
else. Idioms that turn a negator into a yes ("don't hesitate to merge")
are listed in the negator's own regex, as data. `also_if_matches` lists the
other ways a block says the same thing. A sentence the check cannot parse is
refused and rewritten, never let through.

## Why
The commands exist to save the person a sentence, and a session that
needs the exact phrase turns them back into a password: a clear yes in
other words gets answered with a question, and the interruption the
command was meant to remove comes back. A check that reads only words
fails the other way: it lets an order through because a "no" sat
somewhere on the line, or stops a report of the past as if it were an
order.

## Story
**2026-09-16.** Alex argued that a session should read for intent rather
than scan for the keyword. Morgan agreed, and set the line for the serious
ones: where the exact phrase is not used, use judgment, and ask when in
doubt. [weak-yes](weak-yes.md) and `go-update` were revised that day.

**2026-09-28.** Adding two synonyms to the landing command, Morgan: *"don't
just literally look at the words but think about the words I say, the
context, what we had been discussing."*

**2026-10-08.** The ladder set's landing rule skipped any line holding
"no", "not", "never" or "without", so a paste block saying "Merge it into
main, no questions asked" would have handed landing to another session
with nobody's word in it. Morgan: *"shouldn't it understand the intent
behind commands not just the literal words? This is an important principle
(maybe it should be a practice / principle, to always look for intent) and
don't we already have a practice that does that?"* There was none: the
principle sat in pieces, in the places the Detail lists. This file is the
one place, and the check now judges negation per clause and reads the
other words a block can land with.

## Install
Nothing to install. The occasion index line is generated from this file.
The one mechanical piece is the reply check's landing rule
(`prompt-please-landing-authority` in `reply_check.json`, and the ladder
set's own copy), which uses the two keys the Detail describes.
