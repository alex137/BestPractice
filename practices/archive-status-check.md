---
slug:        archive-status-check
title:       "\"Archive\" and \"Archive?\" both check what's outstanding first, then act"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Same locus as `archive-command`: a phrase (or its plain-language equivalent) in a MESSAGE, not a file path. Decided: 2026-09-18, coined alongside archive-command as its intent-checking counterpart."
occasion:    "a message says \"Archive\" or \"Archive?\", or asks whether the session can be archived"
gates:       ["reply"]
gates_why:   "The check and the resulting archive-or-report both land in the reply, the same turn the question was asked."
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
  decided. Amended 2026-10-12, Alex, adding condition 4 -- nothing from the
  conversation lives only in the chat -- with the-boildown: \"the boildown
  should tell the user what work is not yet in a document and suggest places
  to put it\". Authorized: \"yes, add it upstream\". strength: decided. Amended
  2026-10-19, Morgan, adding condition 5 -- a multi-step plan with steps
  left holds the session open: \"You cannot tell me to archive it unless
  the plan is fully complete Or I explicitly tell you that I am finishing
  the plan early.\" strength: decided. Amended the same day, Morgan, making
  his four-part test the standing rule: \"That should be the standing
  rule\". strength: decided. Amended 2026-10-29 from Morgan's Root issues
  run of 2026-10-28, which found a worker session that archived itself
  with a message from its parent session still unread: condition 2 now
  reads the notifications waiting for this session first. strength:
  assented."
strength:    decided
---
## Rule
When a message says **"Archive"** -- with or without a question mark, alone
or ending a sentence -- or asks in substance whether the session can be
archived or anything is still outstanding, **run the check right then, in
that same turn, and act on what it finds.** The bare word does not skip the
check.

**The test, in Morgan's words, is under "The standing test", in Detail**:
nothing pending, nothing unpushed, nothing needed in temporary files, and
the plan continued elsewhere or dropped. It is
[the-boildown](the-boildown.md)'s four archive conditions and its plan
blocker, run on demand (in full under "The five conditions in full"):

1. **Nothing in the container anybody wants would be lost**, in every
   checkout it holds. Run
   [tools/precedent_container_safe.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_container_safe.py)
   and read its answer, which decides the verdict rather than qualifying
   it; stop each command still running, or wait for it.
2. **Nothing is left to do in this session**, a message from another
   session included: read every waiting notification first
   (`ReadNotifications` in Claude Code) and act on each one.
3. **No Routine is bound to this session** (`list_triggers`).
4. **Nothing from the conversation lives only in the chat.** Re-read all
   of it, compacted parts included, against the committed files, and list
   anything missing with a suggested home and an offer to put it there.
5. **No multi-step plan this session is following has a step left**,
   unless the person says in their own words they are ending it early, or
   it is handed to a session confirmed running with it.

**All five hold, and nothing else is worth flagging -- archive it**:
resolve the session, check `list_triggers`, call `archive_session`, and say
plainly that it's done and that `unarchive_session` reverses it.

**Anything is outstanding -- do not archive.** Say plainly what it is, and
leave the decision with the person. Work already on the landing branch but
not on `main` gets a one-line note and does not hold the archive.

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

Everything under the headings below from "The phrase in full" on was the Rule's own text until 2026-10-31, moved here whole when the Rule was cut to what a session must do (Story, 2026-10-31). The Rule names each heading where it needs it.

### The phrase in full

When a message says **"Archive"** -- with or without a trailing question
mark, standing alone or as the tail of a sentence -- or asks, in substance,
**"can I archive this, or is something still outstanding"** in plain
language ("are we good to close this out", "anything left before I move
on", "is this one done") -- **run the check right then, in that same turn,
and act on what it finds.** The bare word does not skip the check: the
old immediate-action reading of a standalone `"Archive"` is retired, and
both spellings resolve to this one rule.

### The standing test

**The standing test, in Morgan's words** (2026-10-19, strength: decided):
*"if a session has nothing else pending, nothing that wasn't pushed to
[the landing branch], nothing on in the temporary files that's needed, and the plan is
being continued in another session, or I said that I don't want to
continue the plan, then you can say, and you should say, it can be
archived."* The conditions below are that test, spelled out; when they
hold, say so.

### The five conditions in full

**The check is [the-boildown](the-boildown.md)'s own four archive
conditions and its plan blocker, run on demand instead of waited for at the
natural end of a reply:**

1. Nothing in the container that anybody wants to keep would be lost --
   **every checkout it holds, not just the one this session worked in**.
   Run [tools/precedent_container_safe.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_container_safe.py)
   and read its answer rather than recalling what was pushed. It also lists
   any command this session started that is still running: archiving kills
   it, so stop each one with nothing left to do, or wait for it.
2. Nothing is left to do directly in this session, **a message from
   another session included**. Read every notification waiting for this
   session first (`ReadNotifications` in Claude Code) and act on each one;
   one still waiting holds the archive. A session archiving itself is the
   case this catches: on 2026-10-28 a worker archived itself while its
   parent's message sat unread, and that task was lost.
3. No Routine is bound to this session (`list_triggers`).
4. Nothing from the conversation lives only in the chat. Re-read the
   whole conversation, the summary of any compacted part included, and
   check every idea, decision, finding and open question against the
   committed files. Anything not in a document is listed, each with a
   suggested home and an offer to put it there, along with any
   restructuring of this session's own documents that would make them
   clearer or give that material a home, including a recorded
   decision whose substance belongs in the document it shapes --
   the-boildown's condition 4.
5. No multi-step plan this session is following has a step left. A plan
   holds the session open until every step is done, or until the person
   says in their own words that they are finishing it early, or until it
   is handed to another session confirmed running with it; name the plan
   and what is left, in plain words (the-boildown's blocker 5, Morgan,
   2026-10-19).

### Archiving, and the scanner's answer

**All five hold, and there is nothing else worth flagging** (no open
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

### When something is outstanding

**Anything is outstanding -- do not archive.** Say plainly what it is: a
merge into the landing branch still open (never a Produce or a move into
`main`: work already on the landing branch gets a one-line note that it is not on
main, and the archive goes ahead, per [the-boildown](the-boildown.md)),
something the assistant is waiting on, a recommendation worth hearing
before the person moves on to something else. Leave the decision
with the person; this phrase asks a question, it does not answer itself.

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
`go-update`'s was.

**Amended 2026-09-19**, folding the bare `"Archive"` trigger in under the
same check. Morgan: *"Note that 'Archive' and 'Archive?'
are the same thing. Even with no question mark, you should first check to
see what's outstanding and if there is anything, tell me to make sure I
want to archive it."* (strength: decided). `archive-command` is
deduplicated into this file as of the same change, rather than retired
outright, because the word itself is still wanted -- only the
skip-the-check behavior it used to carry is gone.

**2026-10-31: the Rule cut to what a session must do.** The Rule had grown to 707 words; it now holds the trigger, the five conditions and the two outcomes, in 322 words (both counted with `wc -w` over the section). Every paragraph it held moved word for word into Detail, under the headings the Rule names, Morgan's standing test included; nothing was deleted. Morgan asked for the longest Rules to be reviewed and shortened this way, and approved it (strength: assented); his words are in [todo-2026-10-30-very-deep-check-findings](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-10-30-very-deep-check-findings.md).

## Install
`get_session` to resolve this session's own ID, `list_triggers` for a
Routine bound to it via `persistent_session_id`, and `archive_session`
when the check comes back clear. A session on a provider with no
equivalent tool calls has no way to carry out the archiving half -- say so
plainly, rather than guessing at a substitute.

No mechanical check, same class as [park-it](park-it.md): this governs
how a message is read and whether a conversation's own state (a pending merge, an open
recommendation) is genuinely clear, neither of which a repo-scoped script
can see. The one place either judgment is visible is the conversation
transcript itself.
