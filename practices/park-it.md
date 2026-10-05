---
slug:        park-it
title:       "\"Drop it\" marks an item parked and ends the subject"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A moment, and specifically a phrase in a MESSAGE -- no file path reaches it. Routed by the `reply` gate. Decided: 2026-09-08, when it moved up from the repo-local source."
occasion:    "a person says \"Drop it\" about an open item or a question"
gates:       ["reply"]
gates_why:   "The obligation lands in the reply: mark the item this turn, say which one, ask nothing back."
index_clause: "mark the item `parked` now; never raise it unprompted again"
checked_by:  null
ships:       ["tools/todo_disposition.py"]
defines:     ["Drop it"]
command:     {"Drop it": "Mark the open question as parked and drop the subject. It won't be raised again unless you raise it."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08 -- coined the same day, moved up to universal the same day"
---
## Rule
When the person says **"Drop it"**, park the item they mean **in that same
turn**, and no session raises that item unprompted again -- not this one,
and not a later one that decides it has become urgent.

**A park is written in two places, and a tool writes both.** In a per-item
`todo/todo-*.md` file run `python3 tools/todo_disposition.py park SLUG --by
NAME`: it sets the frontmatter `disposition: parked`, which is what every
reader acts on, and adds `**Disposition:** parked (<date>, <who said it>)`
to the body, which records who and when. In a single `TODO.md` the body line
is the whole record. NAME is the person's own word in that session; when
nobody knows, it is `who not recorded`, never a guess.

**They owe no explanation for parking something, and the session asks no
follow-up question about the item.** The phrase exists to end a
conversation, not to open one. The response is to do it and say which item
was marked.

## Detail
**The item they mean is the one the thread is about.** If two are genuinely
in play, park the one under discussion and say in one line which anchor was
marked -- a wrong guess then costs three words to correct rather than a
re-explanation.

**"Drop it" can arrive about something not yet written down at all.** Then
write the item first and mark it `parked` in the same commit:
[repo-is-memory](repo-is-memory.md) does not bend, and parked is not the
same as forgotten.

**When a practice says the item must keep being raised, park it anyway,
then raise the conflict once.** The person's word is carried out first and
never argued with beforehand. Then, in the same reply, one question -- not
about the item but about the practice: *"You dropped this, but
[practice] says it should keep coming up -- should the practice change, or
is this a one-off?"* Run the park with `--conflict PRACTICE` so the item
records that the question was asked; a later session that finds that line
never asks it again. Spotting the conflict is the session's own reading of
the practices in force; the tool only remembers that it was raised.

**Unparking belongs to the person who parked it.** A later session that
thinks a parked item has become urgent may act on the item's content if the
work in front of it needs that, but does not put the question back to them.

**Kept to the literal phrase, deliberately, unlike most of this catalogue's
other commands.** Parking has no built-in correction: it is silent by design
and nothing surfaces a wrongly-parked item again on its own, so a guessed
intent that misses costs exactly the thing [repo-is-memory](repo-is-memory.md)
exists to prevent -- a real concern nobody raises twice. Where the words
plainly are the phrase, act on it; where they only sound like it -- "let's
not worry about that one", "that can wait" -- ask which they mean rather than
guess, the same way a request to land work asks about the object, never
the phrasing, when several things are genuinely in play.

What `parked` then means, and the two other dispositions an open item can
carry, is [open-item-disposition](open-item-disposition.md)'s: an item with
no disposition is `wait`, and a session raises an item only if it says
`ask`.

## Why
A standing phrase costs two words instead of a re-explanation, and it
survives the session that heard it. The failure worth not repeating is the
one "Go merge" already recorded: a session that had not read the definition
went and asked what the phrase meant, which is precisely the interruption
the phrase was invented to stop. **So a phrase is only worth having if it is
written where a session reads before it works** -- which is the argument for
shipping it with the engine rather than leaving each person to invent and
document their own.

The problem it solves is narrower than "stop asking me things": a minor,
genuinely undecided question raised repeatedly in one day by parallel
sessions, each of which was individually behaving correctly. Nothing was
wrong with any one of them. The fix has to be a mark on the item, because
that is the only thing all of them read.

## Story
**Coined by Morgan, 2026-09-08**, in the conversation that produced
[open-item-disposition](open-item-disposition.md). Offered a phrase for
setting an item to `parked`, he answered: *"'Park it' is a fine phrase, and
put it in the glossary."*

**The glossary half was reversed later the same day** -- *"Don't put it in
the glossary"* -- which is why this practice's `defines:` was cleared once
and then restored on the move: the phrase is a term this catalogue defines,
and what he declined was a separate list of disposition words. Recorded
because the two instructions read as contradictory unless the order is
stated.

It lived for one day as a repo-local practice in Precedent's own tree, with
a paragraph in its own Detail explaining that it was at the wrong level on
purpose -- one person's phrase, recorded there only because a session rooted
in that repository could not reach the private individual set to put it
anywhere better. **Moved to universal 2026-09-08**, along with `go-update`,
on Morgan's decision that these are the project's own commands rather than
one person's habits: *"we should have our own commands we use for people who
live in our universe."*

**2026-09-16: kept on the literal phrase, as a session's own judgment call,**
in the conversation where Morgan asked for intent-recognition to widen
across the command set generally, and for `go-update` and `weak-yes`
specifically to gain an ask-if-in-doubt step. This one takes neither change:
widening it risks a false trigger that never surfaces itself again, which
neither of those two risks.

**Renamed to "Drop it" on 2026-09-20.** Morgan doesn't say "park" in
conversation; he said so directly and asked for the phrase to match how he
actually talks. The mechanism this practice defines is unchanged — same
trigger-word discipline, same `parked` disposition it writes, same
never-raise-it-again guarantee — only the word he says is different. The
2026-09-08 and 2026-09-16 quotes above are left as spoken; they are what
was actually said about the phrase "Park it" while that was still its name.

**2026-10-05: one writer for both copies, and the conflict question.**
Until then the Rule named only the body line, while
[`tools/build_todo_index.py`](https://github.com/alex137/BestPractice/blob/staging/tools/build_todo_index.py) and every other reader acted only on the
frontmatter field, and nothing checked that the two agreed. Every park so
far had been typed by hand; sessions had happened to write both, but two
parked items recorded nobody's name, and one no date either, and a session following the
Rule's words literally would have left the frontmatter at `ask` -- the item
it was told to drop would have kept coming up. The same day Morgan asked for
the conflict case: *"since morgan/the user said to drop it, but such-and-such
Practice says I should not drop it, therefore, have a session conversation
with morgan about that conflict because, perhaps, we should update the
practice?"* Recorded in
[spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md](../spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md).

## Install
[`tools/todo_disposition.py`](../tools/todo_disposition.py) ships with this practice. The
`open-item-disposition` check in [`tools/precedent_check.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py) backs it up: a
park with no dated, named body line is reported, and so is a body line that
disagrees with the frontmatter -- hardest when the body says parked and the
frontmatter still says `ask`.

Nothing mechanical checks that the phrase was *honoured* -- that lives in
the conversation rather than in the tree. What a repository
can check is that the phrase is documented where its own sessions actually
read, which is what Precedent's own repo-local `check_park_it.py` asserts
against its `AGENTS.md`. An adopter needs no equivalent: the phrase reaches
every session through the occasion index above, which is generated.
