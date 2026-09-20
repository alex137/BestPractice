---
slug:            gotcha-2026-09-20-a-sessionstart-hook-writing-a-file-is-not-the-session-loadi
status:          live
noted:           2026-09-20
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A SessionStart hook renders a file correctly, every session, and the session behaves as though the file does not exist — because writing a file is not loading it, and Claude Code auto-loads instruction files only.

## Story

**Claude Code puts exactly two things in front of the model before the first
turn: its instruction files, and whatever a hook hands back as
`hookSpecificOutput.additionalContext`.** `CLAUDE.md` is the instruction
file; `AGENTS.md` is read in its place where a project has no `CLAUDE.md` of
its own (2.1.278, `instructionFiles` defaults to `claude-md-or-agents-md`).
**Everything else is a file on disk**, however faithfully a hook regenerates
it and however plainly an instructions file asks for it to be read.

From 2026-09-13 to 2026-09-20 every Precedent practice set rendered
`.precedent/SESSION_PRACTICES.md` at session start — 125 universal practices,
correct, fresh, self-healing against staleness since 2026-09-18 — and no
session loaded it. The only thing pointing at it was one sentence in the
generated Standing Instruction, *"read it too"*, which costs a tool call the
session must decide to make after it has already started working. Three
rounds of fixes landed in those seven days, each aimed one layer lower than
the break: the clone, the render, the pointer, the staleness. **Each round
measured that the file was written and none measured that anything read
it**, and the repository's own always-loaded-surface registry had declared
that file loaded since the first day, which is where anybody checking would
have looked.

**The trap generalizes past this one file.** Anything a hook produces for the
model's benefit — a rendered catalogue, a status table, a probe result — is
invisible unless it comes back through `additionalContext`. The same bug was
sitting one size smaller in the same hook:
`tools/precedent_access_check.py`'s "which repos can this session push to"
table wrote to **stderr** from 2026-09-14, so it reached the transcript a
person might scroll and never the model it was written for.

**Two mechanics that bite when you fix it.** Claude Code parses a hook's
stdout as JSON, so **one stray line printed alongside the object invalidates
the whole thing** — capture every step's stdout and print the object once, at
the end. And an `@import` in `CLAUDE.md` is not an equivalent route for
hook-generated content: imports resolve when instruction files are read,
which can precede the hook's render, so the import loads the *previous*
session's copy, and where the hook also fired the same text loads twice.

## Fix

**Emit it, don't just write it.** The hook renders the file and then prints
one JSON object on stdout carrying the text as
`hookSpecificOutput.additionalContext`; stderr is left for real errors. The
worked version is
[templates/harness/claude-code/hooks/precedent-universal-catalogue.sh](../templates/harness/claude-code/hooks/precedent-universal-catalogue.sh),
and the whole story — including the four reasons it survived seven days of
fixes — is
[spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md](../spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md).

**Test it from outside the session**, since from inside there is no reliable
way to tell what was loaded: run the hook and check that its stdout parses as
JSON and that `hookSpecificOutput.additionalContext` is the size you expect.
