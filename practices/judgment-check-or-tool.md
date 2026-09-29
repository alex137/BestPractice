---
slug:        judgment-check-or-tool
title:       Sort each practice by what carries it -- judgment, a check, or one shared tool
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a second implementation of the same mechanism turns up, or a full practice audit runs"
gates:       []
index_clause: "judgment stays prose; checkable gets an audit; a mechanism gets one tool"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-29"
approved_by: "Alex, 2026-09-29 -- asked in session (\"do we have a practice of checking whether a practice or set of practices is better with this sort of transformation to code and usage guidelines?\"), then \"Ok let's do it\""
strength:    decided
---
## Rule
Every practice is carried by one of three things, and **the practice's
text should say which**:

- **Judgment.** The rule needs a person or a session to weigh something
  that no script can see — framing a document for its reader, when to
  push back, what counts as a small call. It stays prose.
- **A check.** The rule can be broken in a way a script can detect. It
  gets an audit that fails loudly, per
  [convention-to-audit](convention-to-audit.md), and the prose shrinks to
  what the audit does not cover.
- **A mechanism.** The rule is really a procedure — hash these files,
  store this record, lock this branch, retry this push — that sessions
  carry out by hand or that each tool reimplements. **It becomes one
  shared tool, and the practice is rewritten as how and when to use that
  tool.** A procedure written as prose gets done a little differently every
  time; a procedure written as code gets done the same way, and fixed once.

Ask the question at two moments: **when a second implementation of the
same mechanism turns up** — a second hash-and-compare, a second
store-on-a-branch, a second retry loop — and **during a
[full practice audit](full-practice-audit.md)**, for every practice that
has no check.

## Detail
**The trigger is the second copy, not the first.** One implementation of
a mechanism is just code. Two that do the same thing in different words
are where the drift starts: a fix lands in one and not the other, and the
practices that describe them start disagreeing about what the procedure
is. That is the moment to merge them into one engine with thin host
shims ([engine-plus-host-shims](engine-plus-host-shims.md)) — not later,
when there are five.

**Look for the mechanism under different names.** Two tools rarely call
the same procedure the same thing. A "baseline", a "manifest", a "ledger"
and a "fingerprint" can all be *hash these inputs, store the hashes, later
report whether they still hold*. A "lease", a "lock" and a "claim" can all
be *write a small record to a shared branch, with the push as the lock*.
Describe each tool by what it does to its inputs, then compare.

**A practice can be split across the three.** Most are. The usual shape
after the transformation: the mechanism moves into a tool, the checkable
part becomes an assertion in that tool or an audit over its output, and a
short paragraph of judgment stays — when to call the tool, what to do
when it refuses.

**Merging implementations is a design change, not a cleanup.** Each copy
carries decisions the others may lack — one hashes at read time, one
normalizes line endings first, one records the tool's own version. The
merge takes the union of those decisions or states why one is dropped,
and each old caller is moved over with a check that it gets the same
answer on the same input. Write the plan before the code, and let the
owner decide whether to do it.

**Not every procedure is worth a tool.** A step done once a month by one
person, with nothing to drift against, can stay prose. The test is
whether two sessions following the same text could reasonably do
different things, and whether that difference would cost anything.

This practice has no repository-level check (`checked_by: null`): whether
two tools share a mechanism is a reading of what they do, not a pattern a
script can match. The full practice audit is where it is asked.

## Why
Prose procedures drift silently. Each session that carries one out does
it from its own reading, and each tool that reimplements one encodes its
author's reading. The differences show up only when something goes wrong:
a fix that covered one copy, a record one tool trusts and another would
have refused. [convention-to-audit](convention-to-audit.md) handles rules
that can be *checked*; nothing handled rules that should be *executed*,
so the same procedure kept getting written again.

## Story
In the originating repository, a session had just rebuilt one tool — a
ledger that skips a gate's unit when its recorded inputs still hash the
same — and a review had found and fixed half a dozen ways it could be
wrong. The owner then asked whether the repository had two kinds of cache
and whether they should share code. Looking, there were three
mechanisms, not two, and two of them each existed more than once: three
separate "hash these inputs and tell me later whether they still hold"
implementations (the new ledger, a drift check over released documents,
and the manifests stamped on built packages), and two
"store records on a dedicated branch with the push as the lock" tools
that already shared their locking but each carried its own copy of the
git plumbing. The fixes the review had just made to the ledger — hash at
read time, record the tool's own version — did not exist in the other
two. About eight practices turned out to be describing these mechanisms in
prose. The owner then asked whether any practice told a session to look
for this; none did, and this is it.

## Install
Nothing to install. At a full practice audit, add one closed question
per practice without a check: *is this judgment, checkable, or a
mechanism?* When a review or a new tool turns up a second implementation
of a mechanism, write a short plan for the merged engine — what each copy
does, what the union keeps, how each caller is moved and verified — and
put it to the owner before writing the engine.
