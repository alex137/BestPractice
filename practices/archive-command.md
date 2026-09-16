---
slug:        archive-command
title:       "\"Archive\" authorizes archiving the session meant, right now"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message says \"Archive\" standing alone, about a session"
gates:       ["reply"]
index_clause: "\"Archive\" alone means archive the session meant (default: this one) now"
checked_by:  null
defines:     ["Archive"]
command:     {"Archive": "Archive the session meant -- this one, unless another is named -- right now. It's reversible if it wasn't meant."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-16"
approved_by: "Morgan, 2026-09-16 -- coined in his individual set the same day
  and moved to universal on his decision that this is the project's own
  command rather than one person's habit: \"I think this should be a
  universal command not just for me.\" strength: decided."
strength:    decided
---
## Rule
When a message says **"Archive"** -- standing alone, case-insensitive, as its own line or as the whole of a sentence -- treat it as authorization to archive the session it means, **right then, in that same turn: no confirmation, no recap first.**

**Which session it means, unless one is named: the session the message arrived in.** Resolve its own ID (`get_session` with no argument), check `list_triggers` for a Routine bound to it via `persistent_session_id`, and archive it (`archive_session`). A bound Routine does not block this -- the word is the authorization -- but say so in the reply, since an archived session accepts no events and the Routine will stop firing.

**Say plainly what happened and that it undoes.** State that the session is now archived -- read-only, its container released -- and that `unarchive_session` reverses it if it wasn't meant, with the one exception [the-boildown](the-boildown.md) already names: anything uncommitted, or committed but unpushed, in that container's working tree does not come back, because unarchiving provisions a fresh container rather than resuming the old one.

## Detail
**The word has to stand alone, the same test [go-merge](go-merge.md) already applies.** "That's it, thanks. Archive." and a lone line reading `ARCHIVE` both count. "let's go dig through the archive" or "can you archive that file" don't -- there the word is doing ordinary work inside a longer sentence, not standing alone as the message's last (or only) one. Where it's genuinely ambiguous which reading is meant, don't assume: ask.

**This is a different occasion from [the-boildown](the-boildown.md)'s own archive line.** That one is a *recommendation* a session makes on its own judgment, gated by three conditions (work safe elsewhere, nothing left to do, no bound Routine) before it ever suggests archiving. This one is the reverse direction: the person says the word, and the three conditions don't gate it -- a bound Routine gets flagged, not enforced, because the word is the person overriding the judgment call, not asking for it.

## Why
The standing-phrase mechanism already exists for exactly this shape of thing -- [go-merge](go-merge.md), [park-it](park-it.md), [weak-yes](weak-yes.md) -- so a one-word trigger for archiving is the same mechanism, not a new one. Encoding it as a command rather than leaving it to plain conversation is what makes it reach a session that has never talked to the person before but has this set loaded -- the same argument `go-merge`'s own Story already makes about definitions sitting where a session can't read them.

## Story
Coined 2026-09-16 in Morgan's individual set, the same day he asked whether archiving a session works only through the UI or also through a command and, told it works as a direct tool call already, asked for "archive" itself as a standing word.

Moved to universal the same day, on his decision that it belongs alongside the project's other commands rather than staying his own habit: *"I think this should be a universal command not just for me."*

## Install
No mechanical check, same class as [go-merge](go-merge.md): this governs how a message gets read, not a property of a diff or the repo tree, and the one place the distinction between "recognized the word" and "archived on its own initiative" is visible is the conversation transcript, which a repo-scoped script can't read.
