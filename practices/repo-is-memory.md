---
slug:        repo-is-memory
title:       The repo is the memory; sessions are ephemeral
tier:        resident
severity:    default
applies_to:  ["**"]
applies_to_why: "Resident; its applies_to is not this file's business. Decided: phase 4 routing pass."
occasion:    "starting any session cold"
gates:       ["reply"]
gates_why:   "A turn ending is when knowledge either got committed or was lost."
index_required: false
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 1
---
## Rule
Everything a future session needs — orientation, open items,
decisions, lessons — lives in committed files. A session's chat thread is
disposable; if knowledge exists only in a thread, it is already lost.

**So does the work itself.** A draft, a summary, generated output, a script
or a result a session was asked to make goes on its feature branch and is
pushed in the turn it is made; a scratch folder holds intermediate steps,
never finished work waiting to be filed. When it cannot get there -- a check
refuses, access is missing -- the reply's first line says it is in no
repository yet, where it is, and asks how to get it in; never a bare
"held". Secrets and raw private source material (a message's original
words, an unedited transcript) stay out, because git history keeps them;
the reply names anything left out on purpose, and why.

## Detail
**Why the work clause sits here and not in a practice of its own.** The
first paragraph was written about knowledge -- what a session learns -- and
said nothing about what a session makes. A file built in a scratch folder
is neither in a thread nor committed, so nothing told a session that leaving
it there was a failure rather than a pause. Morgan asked for the rule as an
addition to this one, not a new practice (2026-10-11, strength: decided).

**What it does not change.** [findings-return-through-repo](findings-return-through-repo.md)
still covers a finding meant for another session; this covers the work a
session was asked for. "Was asked to make" is deliberate: a conversation
that has not authorized work yet writes nothing, and this clause does not
make it. The archive line's container check in [the-boildown](the-boildown.md)
still decides whether a session may be archived, and since 2026-10-11 it
reads every scratch folder as well as every git checkout: a file left in
one holds the archive line until it is filed in a repository or given up
by name (`**Checkout disposition:** scratch:<session> -- discard
(reason)`). That check only runs at the close; this clause is what covers
the hours before it, when the work is sitting there and the person cannot
tell where it is.

**The exception is narrow on purpose.** It covers secrets and the raw words
of private sources, which are very hard to remove once in git history. A
summary, an extract or a cut transcript made from them is work, and goes in
like any other. Anything left out under the exception is named in the reply
with its reason, so the person can see it and overrule.

## Why
Agent sessions (and humans returning after a month) start cold.
Repos that kept context in threads paid a re-derivation tax every session —
re-finding files, re-learning environment quirks, re-making settled decisions.

## Story
No single dated incident was recorded, because the failure this prevents is
continuous rather than punctual: **repos that kept context in threads paid a
re-derivation tax every session.**

The tax is concrete and itemisable -- re-finding files, re-learning
environment quirks, re-making decisions that were already settled once. Each
individual instance looks like ordinary startup work rather than like loss,
which is exactly why it can run indefinitely without anyone costing it.

The rule's sharpest clause is the one that makes it actionable: **if
knowledge exists only in a thread, it is already lost.** Not "at risk of
being lost" -- already, because nothing about a thread's contents is
reachable by the next session, and the moment of loss has therefore already
passed by the time anyone would think to look.

Agent sessions start cold every time, and a human returning after a month is
in the same position. That symmetry is why this is not an agent-specific
accommodation.

**2026-10-11: work left in a scratch folder.** A session in a consuming repo
built 189 one-line summaries of company activity in its scratch folder,
outside every repository, meaning to file them into the repo next. The
filing step was refused by the harness's permission check; the session
reported "filing held" and moved on. The summaries sat outside any repo for
hours, and the person could not tell where they were: *"EVERYTHING MUST GO
INTO A REPO. Isn't the way we always work that you create a temporary
[branch] and put them there, then I merge that into staging?"* Morgan, same
day, agreed the rule was right and asked that it extend this practice rather
than start a new one (strength: decided). The second paragraph of the Rule
is that extension.

## Install
The three living documents below (MAP, TODO, GLOSSARY) plus a
project instructions file (`AGENTS.md`, plus a per-harness pointer file —
see [session-bootstrap](session-bootstrap.md)). Everything else in this
catalog is a refinement of this rule.
