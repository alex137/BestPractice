---
slug:        archive-status-check
title:       "\"Archive\" and \"Archive?\" both check what's outstanding first, then act"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message says \"Archive\" or \"Archive?\", or asks whether the session can be archived"
gates:       ["reply"]
index_clause: "check pending; archive if clear, else say what isn't"
checked_by:  null
defines:     ["Archive", "Archive?"]
command:     {"Archive": "Check whether anything from this session is still outstanding -- a merge, something the assistant is waiting on, a recommendation -- and either archive it right then or tell you exactly what's left.", "Archive?": "Check whether anything from this session is still outstanding -- a merge, something the assistant is waiting on, a recommendation -- and either archive it right then or tell you exactly what's left."}
status:      active
in_force_at: null
supersedes:  ["archive-command"]
overrides:   null
added:       "2026-09-18"
approved_by: "Morgan, 2026-09-18 -- dictated in full, including the reading
  that other wording carrying the same feeling counts too. strength: decided.
  Amended 2026-09-19, folding in the bare \"Archive\" trigger under the same
  check: \"Note that 'Archive' and 'Archive?' are the same thing. Even with
  no question mark, you should first check to see what's outstanding and if
  there is anything, tell me to make sure I want to archive it.\" strength:
  decided. `archive-command` is deduplicated into this file as of the
  same change. Amended 2026-09-22, Morgan, restating condition 1 as the
  whole container rather than this session's own work, after a reply cleared
  its own eight commits and left six unpushed in a source clone: \"only say
  you can archive this when nothing in the container that we want to keep
  will be lost and I have pushed or merged everything we need to\". strength:
  decided."
strength:    decided
---
## Rule
When a message says **"Archive"** -- with or without a trailing question
mark, standing alone or as the tail of a sentence -- or asks, in substance,
**"can I archive this, or is something still outstanding"** in plain
language ("are we good to close this out", "anything left before I move
on", "is this one done") -- **run the check right then, in that same turn,
and act on what it finds.** The bare word does not skip the check: the
old immediate-action reading of a standalone `"Archive"` is retired, and
both spellings resolve to this one rule.

**The check is [the-boildown](the-boildown.md)'s own three archive
conditions, run on demand instead of waited for at the natural end of a
reply:**

1. Nothing in the container that anybody wants to keep would be lost --
   **every checkout it holds, not just the one this session worked in**.
   Run [tools/precedent_container_safe.py](../tools/precedent_container_safe.py)
   and read its answer rather than recalling what was pushed.
2. Nothing is left to do directly in this session.
3. No Routine is bound to this session (`list_triggers`).

**All three hold, and there is nothing else worth flagging** (no open
recommendation, no other live session on the same subject, nothing the
assistant is itself waiting on) -- **archive it**: resolve the session,
check `list_triggers`, call `archive_session`, and say plainly that it's
done and that `unarchive_session` reverses it.

**The scanner's answer is not a caveat to report alongside an archive
verdict -- it decides the verdict.** Unpushed work anywhere in the container
fails condition 1 outright, whoever's work it is and whichever clone it sits
in; push or merge it first, or say plainly that it is meant to be lost. A
reply that says the archive sentence with the container unsafe is refused by
the reply gate ([the-boildown](the-boildown.md)'s
`require_container_safe_if_says`), which is the 2026-09-22 amendment below.

**Anything is outstanding -- do not archive.** Say plainly what it is: a
merge still open, something the assistant is waiting on, a recommendation
worth hearing before the person moves on to something else. Leave the
decision with the person; this phrase asks a question, it does not answer
itself.

## Detail
**This absorbs `archive-command`'s old job.** That practice used to mean
the bare word overrides the judgment call -- the three conditions got
flagged, never enforced, because the person saying just "Archive" was
taken as having already decided archiving was fine. Morgan withdrew that
distinction on 2026-09-19: the two spellings feel the same to him, and he
wants the check run every time, question mark or not. `archive-command` is
now `deduplicated` into this file rather than describing a live behavior
of its own -- a session that still archives on a bare `"Archive"` without
running the check first is doing the retired reading, not this one.

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

**Amended 2026-09-19**, folding the bare `"Archive"` trigger in under the
same check. Morgan: *"Note that 'Archive' and 'Archive?'
are the same thing. Even with no question mark, you should first check to
see what's outstanding and if there is anything, tell me to make sure I
want to archive it."* (strength: decided). `archive-command` is
deduplicated into this file as of the same change, rather than retired
outright, because the word itself is still wanted -- only the
skip-the-check behavior it used to carry is gone.

## Install
`get_session` to resolve this session's own ID, `list_triggers` for a
Routine bound to it via `persistent_session_id`, and `archive_session`
when the check comes back clear. A session on a provider with no
equivalent tool calls has no way to carry out the archiving half -- say so
plainly, rather than guessing at a substitute.

No mechanical check, same class as [go-merge](go-merge.md): this governs
how a message is read and whether a conversation's own state (a pending merge, an open
recommendation) is genuinely clear, neither of which a repo-scoped script
can see. The one place either judgment is visible is the conversation
transcript itself.
