---
slug:        brief-it
title:       "\"Brief it\" hands another session a self-contained briefing: the situation, this session's id, a recommendation, and which repos to seed"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person asks, in whatever words, for a write-up of the current issue that they can hand to other sessions"
gates:       []
index_clause: "\"Brief it\" -- one paste block: situation, session id, recommendation, repos"
checked_by:  null
defines:     ["Brief it"]
command:     {"Brief it": "Write up the current issue or situation as a self-contained briefing for a session that was not in this conversation -- what happened and the context behind it, this session's own id and a link to it, what you recommend the other session do and why, which repository has to be its primary seed root, and which others (if any) need to be attached alongside it -- and hand the whole thing back as one block ready to copy in one click."}
status:      deduplicated
in_force_at: my-options
supersedes:  []
overrides:   null
added:       "2026-09-19"
approved_by: "Morgan, 2026-09-19 -- described the command in full and proposed
  \"options\" as its trigger word. The session flagged that this collides with
  my-options.md's own trigger, \"My options\" -- an unrelated command, about
  laying out decision choices -- and substituted \"Brief it\" instead, disclosed
  in the same reply rather than decided by him. Authorized in full: \"Go update.\""
strength:    assented
source_practice_number: null
---
## Rule
**"Brief it" is the clean form, not the only one** -- "write this up so I can
hand it to another session", "give me something I can paste into another
window about this" and anything else that plainly asks for the same shape of
answer get the same treatment, recognized by what is being asked for rather
than by matching the phrase.

Produce one self-contained briefing, with all of the following, every time:

1. **The situation.** What happened and the context that led to it, written
   for a reader with none of this conversation -- the same completeness
   [write-it-up](write-it-up.md) asks for.
2. **This session's own id and title, with a link, and that a session wrote
   it rather than a person** -- the same header
   [seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md)
   requires of any prompt one session hands to another, because whoever
   reads this needs to know where the claims came from.
3. **A recommendation, with the reason.** What you think the other session
   should do, named plainly -- not a survey that leaves the choice sitting
   there. The same discipline [my-options](my-options.md) already states:
   the recommendation is the part that gets dropped, and it is the part
   asked for.
4. **Which repository has to be the primary seed root** -- the one the
   receiving session needs opened or rooted in for the recommendation to be
   actionable at all.
5. **Which other repositories, if any, need to be attached alongside it.**
   Say "none" explicitly when that is the honest answer -- never leave the
   reader to guess whether the question was even asked.

**Delivered as one block, ready to copy in one click** -- nothing split into
the surrounding prose, nothing left for the reader to assemble from several
paragraphs. This is [the-boildown](the-boildown.md)'s own requirement for any
handoff, carried forward here: the words are the session's to write, not the
reader's to compose.

**It does not, by itself, authorize anything in the repository or repositories
it names.** Producing the briefing is not committing, pushing, or merging
anything -- whatever the receiving session goes on to do there follows
whatever authorization already governs that repository, exactly as
[write-it-up](write-it-up.md) draws the same line around its own report.

## Detail
**Where this differs from [Write it up](write-it-up.md).** That command's
deliverable is a file committed to the repo, reached by a link -- durable,
but a click away. This command's deliverable is the text itself, meant to be
pasted directly into a different window with nothing to click through.
Nothing stops using both on the same issue -- write it up for the permanent
record, then Brief it for what actually gets handed elsewhere -- but Brief
it does not depend on a commit existing first, and does not make one.

**Where this differs from [Session Text](session-text.md).** That command
decides whether the work THIS session is currently doing belongs in a
different session, and produces the opening text for a window that does not
exist yet. Brief it is not about relocating unfinished work -- it is a
report on a situation already understood, for a reader (a session, existing
or new) who has to evaluate it and decide what to do. The repository-naming
discipline is the same for a reason: whichever session opens the block still
needs the two facts Session Text always supplies -- what to root itself in,
and what else it needs attached -- even though nothing here is being
relocated.

**The recommendation is not optional even where the honest answer is
uncertain.** Say what you would do and why you are not certain, rather than
dropping the recommendation because the case is not clean -- a briefing that
lays out the situation and stops has handed the comparison back to whoever
reads it, with less context than the session that just did the work.

## Why
The reason to ask for this is the same one [write-it-up](write-it-up.md)
already names: handing a problem to someone who was not in the conversation
means the write-up has to stand on its own. What write-it-up does not cover
is the shape asked for here -- a chat-delivered, paste-ready block that
names this session, picks a recommendation, and says which repositories the
reader needs -- rather than a file to click through to, or a check on
whether the session's own current work should move.

## Story
Coined by Morgan, 2026-09-19. He described the command in full before naming
it: write up the issue found, with the context and situation, what happened,
this session's own id, a recommendation for other sessions and the reason
for it, which repo needs to be the primary seed root, and which others (if
any) need to be attached -- delivered wrapped for one-click copying. Asked
for a short trigger word, he proposed "options" himself and approved it in
the same breath.

The session raised a collision before building it: "options" sits directly
against [my-options](my-options.md)'s own trigger, "My options" -- a command
about laying out decision choices, nothing to do with briefing another
session on an issue. AGENTS.md's own precedent-commands section states the
design this would break: "each has a phrase that is always sufficient and
never ambiguous." "Brief it" was used instead, matching the "<verb> it"
shape [Drop it](park-it.md) and [Write it up](write-it-up.md) already use,
and checked against every trigger phrase already in force in this catalogue.

**Deduplicated the same day, into [my-options](my-options.md), on Morgan's
decision.** Reading this file, he turned "Brief it" down on both the name and
the split: *"I hear 'brief' and I think something bigger and more formal in
github -- which is exactly what we did a few days ago with the command
'write it up'! This is more something to paste in, something smaller and
shorter... I still like 'my options' and then it triggers when you realize
it's similar to 'show me options' etc. Let's use that."* The shape this file
described -- the situation, the session id, the repositories, the
paste-ready block -- moved into `my-options.md` as its handoff case, framed
per his instruction as options to prevent or resolve the issue rather than a
single flat recommendation. Two active practices could not both own the
trigger phrase "My options", so folding this one in rather than keeping a
second file with the collision restored was the session's call, not put to
him.

## Install
Nothing for an adopter to set up -- the phrase reaches every session through
the generated occasion index, the same as any other command declared with a
`command:` field.

**No mechanical check, and the reason matches
[write-it-up](write-it-up.md) and [my-options](my-options.md).** The thing
this governs is a chat reply, never a file the tree holds, so whether a
given reply actually recognized the request and assembled the five required
pieces is a judgment call on the conversation -- not a property
[precedent_check.py](../tools/precedent_check.py) or any other script
watching the tree could read off a diff.
