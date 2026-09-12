---
slug:        spawn-session
title:       "Check whether the work belongs in another session before starting it, and hand over a seeded link"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "handing the person work to do, or starting work that may touch a repository this session cannot reach"
gates:       ["reply"]
index_clause: "cross-repo check first; hand over a clickable seeded session, not a description"
checked_by:  null
defines:     ["Spawn session"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-11"
approved_by: "Morgan, 2026-09-11 -- coined and placed at universal in the same message"
strength:    decided
source_practice_number: null
---
## Rule
**Before starting the work you were just asked for, check whether it belongs
in a different session — and check the repositories first.** Name the
repositories the work has to read, write or push to, and compare that list
against the ones this session actually holds. Everything else that might
argue for a fresh session — a poisoned context, a different branch, a long
run you do not want to block on — comes after that, because a missing
repository is the one this session cannot fix from the inside.

**If a different session is needed, do not start the work and do not
describe the handoff. Create the session** — rooted in the right repository,
already carrying the prompt you would have given it — **and put its link
near the top of the reply, on its own line, telling the person plainly to
click it.**

**The check is unconditional.** It runs whenever another repository might be
involved, whether or not anyone says anything. **"Spawn session" is the
explicit command** for the times it did not: it means *run that check now,
say what it found, and hand me the link* — including when the honest answer
is "this session is the right one", which is said in one line and then the
work continues.

## Detail
**Cross-repository is first because it is the one that gets discovered too
late.** A session learns it cannot reach a repository at the moment it tries
to write there, which is after the reading, the reasoning and the context
that would have made the work cheap — and none of that moves to the session
that *can* write. Worse, some of it cannot be repaired mid-flight at all:
this repository's own gotchas record `add_repo` refusing a cross-owner
attach, so a session rooted under one owner may simply never reach the
other's repositories for its whole life.

**What "create the session" means concretely, as of 2026-09-11.** Where the
harness offers a session-creating tool — in Claude Code's cloud sessions
that is `create_session` on the `claude-code-remote` server — call it with
the target repository as the source and the whole handoff as the prompt, and
the link is the returned session's `https://claude.ai/code/<session id>`
page. **Where no such tool is available, say so and fall back to
[handoff-is-pasteable](handoff-is-pasteable.md)'s paste block** — one or the
other, never silence and never a prose description of what the person should
go type.

**The seeded prompt is a handoff, and
[handoff-is-pasteable](handoff-is-pasteable.md) governs its contents
unchanged**: the session opening that link cannot see this conversation, so
the prompt names the branch, the files, the command and the outcome
expected, and ends with the line to paste back here when it is done. One
session per destination repository, keyed by the repository's name — never
by an ordinal.

**Say what the new session will do before the link.** The person is
authorizing it by clicking, and a link with no sentence attached asks them
to authorize something they cannot see.

**Do not spawn a session for work this session can do, and establish the
verdict rather than inferring it.** The check is a probe, not a hunch: try
the attach, or `git push --dry-run` against the repository, and quote what
came back. *"I am probably not allowed"* is not a finding, and neither is
*"this session looks like it is ending"* — both hand the person back a job
they asked for. Every clean session costs them a tab, a fresh context and a
re-read, so the handoff is normally **partial**: whatever this session can
finish, it finishes here, and only the residue is seeded into the link.

## Why
The cost being avoided is not confusion, it is re-derivation. A session that
works for an hour and then finds the repository out of reach has produced
context, not work, and context is exactly the thing a handoff cannot carry.
Checking first costs one comparison of two lists.

**A click is better than a paste where a click is available**, and that is
the whole delta over [handoff-is-pasteable](handoff-is-pasteable.md). That
rule already says the person is the transport and their load should be a
block of text rather than a task to reconstruct; this one says that when the
harness can create the session directly, their load should be a link rather
than a block of text — the paste block stays as the fallback, not as the
target.

**The command exists because the check is a session's job and the person is
the one who notices it was skipped.** Naming the phrase gives them two words
to force it, instead of explaining the whole thing again in the session where
it matters.

The return path is still [findings-return-through-repo](findings-return-through-repo.md)'s:
a spawned session cannot message this one back, so whatever it learns goes
into its repository, and the person carries one line saying it worked or what
broke.

## Story
**Coined by Morgan, 2026-09-11**, in his own words: *"When you give me what I
need to do, first look to see if it should be in a different session, and
that includes most importantly checking for cross repo issues first. Then, if
that is needed, then you should create a link to the new session, rooted in
the right repo, and already seeded with the prompt you want to give it, and
telling me prominently to click on it."* He asked for both halves in the same
message — the standing behaviour and the phrase: *"You should do this always,
whenever a new repo might be needed, but also have the explicit command for
when you don't."*

**The failures it is built on are all already in this repository's record.**
`add_repo` has refused a cross-owner attach repeatedly, including as a
session's very first tool call, which is what forces work spanning two owners
to be split across sessions at all. A session ran most of a working day here
with no individual practice source resolved, applying the wrong rules the
whole time and unable to tell. And when the handoffs that condition produces
were finally standardized on 2026-09-10, the rule failed on its first real
use: three paste blocks, correctly headed by repository, were read by their
ordinals instead, and one session spent its entire turn proving that another
session's files did not exist.

Every one of those is downstream of the same moment — the moment a session
starts work whose repository it does not have. **Nothing before this checked
that moment**; the catalogue's rules all began after it had already passed.

**It was called `clean-session` for its first day.** Morgan renamed it on
2026-09-12 — *"Let's rename 'clean session' to 'spawn session'"* — and asked
for nothing else about it changed. He gave no reason and none was needed: the
new phrase names what the command does, where the old one named a property of
the destination that the person saying it cannot check from where they are
standing. The rule, the gate and the routing are untouched; only the words
moved.

## Install
Nothing to configure. The occasion index entry above is generated, so an
adopter installs nothing and every session reads the phrase whether or not
any private source resolved.

No mechanical check, and the reason is the same one
[go-merge](go-merge.md) records: this governs what a session does *before*
it touches the tree, and a session that skipped the check leaves behind
exactly what a session that ran it and found nothing leaves behind — the
work, committed normally. The one artifact it produces, a link in a chat
reply, is not in the repository either. What a repository *can* check is
downstream and already covered by
[handoff-is-pasteable](handoff-is-pasteable.md)'s own gate.
