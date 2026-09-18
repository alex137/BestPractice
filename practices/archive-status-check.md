---
slug:        archive-status-check
title:       "\"Archive?\" checks what's outstanding first, then acts on the answer"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message asks whether the session can be archived, or plainly carries that feeling"
gates:       ["reply"]
index_clause: "\"Archive?\" -- check what's pending first; archive if clear, else say what isn't"
checked_by:  null
defines:     ["Archive?"]
command:     {"Archive?": "Check whether anything from this session is still outstanding -- a merge, something the assistant is waiting on, a recommendation -- and either archive it right then or tell you exactly what's left."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-18"
approved_by: "Morgan, 2026-09-18 -- dictated in full, including the reading
  that other wording carrying the same feeling counts too. strength: decided."
strength:    decided
---
## Rule
When a message asks, in substance, **"can I archive this, or is something still
outstanding"** -- the literal `"Archive?"` (with or without the question
mark, standing alone or as the tail of a sentence), or plain language asking
the same thing ("are we good to close this out", "anything left before I
move on", "is this one done") -- **run the check right then, in that same
turn, and act on what it finds.**

**The check is [the-boildown](the-boildown.md)'s own three archive
conditions, run on demand instead of waited for at the natural end of a
reply:**

1. The work is safe somewhere that is not this session's container.
2. Nothing is left to do directly in this session.
3. No Routine is bound to this session (`list_triggers`).

**All three hold, and there is nothing else worth flagging** (no open
recommendation, no other live session on the same subject, nothing the
assistant is itself waiting on) -- **archive it**, using the same mechanism
[archive-command](archive-command.md) uses (resolve the session, check
`list_triggers`, call `archive_session`), and say plainly that it's done and
that `unarchive_session` reverses it, same as that practice's own closing
line.

**Anything is outstanding -- do not archive.** Say plainly what it is: a
merge still open, something the assistant is waiting on, a recommendation
worth hearing before the person moves on to something else. Leave the
decision with the person; this phrase asks a question, it does not answer
itself.

## Detail
**This is deliberately the reverse of [archive-command](archive-command.md),
not a second way to say the same thing.** That practice's whole point is
that the bare word overrides the judgment call -- the three conditions get
flagged, never enforced, because the person is the one who decided archiving
is fine. Here the person is asking the session to make that judgment call,
so the three conditions gate the action rather than merely being named. A
session that archives on `"Archive?"` without having actually checked has
done [archive-command](archive-command.md)'s job under the wrong trigger.

**"Something else you recommend I do" is in scope, not just the mechanical
three.** The question this phrase answers is broader than the-boildown's own
archive line -- it also covers a practice idea sitting unstated, a Todo worth
a look, another session on the same subject -- anything the closing block
would have surfaced anyway. Answering only the three mechanical conditions
and staying silent on a live recommendation technically passes the check
and still leaves the person exactly as much in the dark as before.

## Why
The bare word `"Archive"` already means act now, no recap -- that is
useful precisely because it removes a question. This phrase is the opposite
shape of moment: the person does not know whether it is safe to close the
window, and answering it with an unconditional archive would be guessing on
their behalf in the one direction that cannot be undone cleanly (an archived
session's container is released; work left uncommitted in it does not come
back). The question deserves a real check, not a reflex.

## Story
Coined 2026-09-18, dictated by Morgan in full: *"if I tell you 'archive?' it
means: 'Can I archive this session, or is there anything else pending from
this session I need to do, such as something to merge, something you are
waiting on, something else you recommend I do, or are we good to archive? I
want to get back to something else' -- you don't need to use those words in
your internal prompt but that's what I'm thinking. And as always, not just
that phrase, but if you think I'm feeling that, or I use other words to
imply something like that."* The intent-reading clause is his own, stated
in the same breath as the phrase itself rather than added later the way
[go-merge](go-merge.md)'s was.

## Install
Same binding as [archive-command](archive-command.md): `get_session` to
resolve this session's own ID, `list_triggers` for a Routine bound to it via
`persistent_session_id`, and `archive_session` when the check comes back
clear. A session on a provider with no equivalent tool calls has no way to
carry out the archiving half -- say so plainly, the same as that practice
does, rather than guessing at a substitute.

No mechanical check, same class as [go-merge](go-merge.md) and
[archive-command](archive-command.md): this governs how a message is read
and whether a conversation's own state (a pending merge, an open
recommendation) is genuinely clear, neither of which a repo-scoped script
can see. The one place either judgment is visible is the conversation
transcript itself.
