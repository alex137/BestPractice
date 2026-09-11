---
slug:        fixture-owns-its-state
title:       A fixture owns every piece of state it asserts on
tier:        on-demand
severity:    default
applies_to:  ["**/*.py", "**/*.sh", "**/test_*", "**/tests/**"]
occasion:    "writing a test, fixture or control that reads or edits state it did not create"
gates:       ["review"]
index_clause: "a fixture that inherits real state is testing the environment too"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08 -- the third instance of this failure in two days"
---
## Rule
**Whatever a fixture asserts on, it must own.** Every environment variable,
config file, git identity, clock, and path that can change the result is
either set by the fixture or unset by it — never inherited and hoped about.

Two moves cover almost all of it:

- **Editing real configuration, merge — never replace.**
  `d['key'] = [mine]` throws away whatever was legitimately there;
  `d.setdefault('key', []).append(mine)` adds to it. The replacing version
  passes everywhere the field happens to be empty, which is every machine
  except the one that matters.
- **Clear the ambient inputs at the top, once.** Not in the fixture that
  happened to notice — a fixture written next month inherits the same
  invisible dependency, and it will not notice.

## Detail
**The tell is a test that passes for one person and fails for another with
no code change between them.** That reads as a flake and is not: it is the
fixture measuring the machine.

**Both directions cost the same hour and only one of them looks like a bug.**
A fixture that inherits state can fail spuriously — annoying, and it gets
investigated. It can also *pass* spuriously, because the inherited state
happened to satisfy the assertion, and then the guard it was written to prove
is simply not proven. Nothing about the output distinguishes that from a
working test.

**A scratch copy is not isolation if you copy the real thing into it.** The
incident below clones a real repository into a temporary directory, which
looks like a clean room — and the clone brings the real `identity.json` and
the real history with it. Isolation is about what the assertion depends on,
not about where the files sit.

## Why
This is the third instance in two days of one shape, which is what promoted
it from a habit to a rule
([mistakes-become-rules](mistakes-become-rules.md)). All three were expensive
in the same way: the failure did not look like an environment problem, so
each one sent a session to debug the mechanism under test instead.

The general form: **a test states a claim about the code, and inherited state
silently widens that claim to "the code, on this machine, today."** Everything
downstream of it — a green gate, a red one, a measurement — is then about
something nobody meant to ask.

## Story
**2026-09-08, the instance that named the rule.** `precedent-individual`'s
`test_buenos_aires_dates.sh` and `test_commit_author.sh` each plant a bad
commit, then write
`d['grandfathered_commit_shas'] = [{'sha': ..., 'note': 'test plant'}]` into
a cloned `identity.json` — **replacing** the list rather than appending to
it. Correct in a repository whose `identity.json` carries no grandfathered
SHAs, which was every repository the fixture had run in. In one that
legitimately carries nine, the write wipes all nine, the check then fires on
seven real pre-existing commits, and the test reports a failure it
manufactured itself. Found from a consumer repo's session during a vendor
update; four sites, not the two first reported.

**The two before it are in [AGENTS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md)'s gotchas, and neither
was recognised as the same problem at the time.** A harness fixture set a
global git identity and asserted commits used it, while `GIT_AUTHOR_*` —
exported by a practice set's own settings — silently outranked it: 4 of 11
stated cases failed, none real, and three failed in the direction that reads
as a broken guard. Separately, `git config precedent.requireVocabulary true`,
set to satisfy one gate, made two of another gate's own cases fail; neither
mechanism said it wanted the opposite environment.

**The fix in all three is the same sentence and it is worth stating plainly:
clear the ambient input at module scope, and merge rather than replace.** The
`GIT_AUTHOR_*` fix deliberately went beside the existing environment scrub
rather than into the one fixture that noticed — a later fixture would
otherwise inherit the same dependency with nothing to warn it.

## Install
No mechanical check. A scan cannot tell a deliberate `d['key'] = value` in
production code from the same line in a fixture clobbering real
configuration, and one that guessed would fire on ordinary assignment
everywhere ([checkable-gets-checked](checkable-gets-checked.md) calls a check
that fires on correct work worse than none). It routes on test paths and
fires at the `review` gate instead, which is where a fixture's inherited
state is actually visible — in the diff that introduces it.
