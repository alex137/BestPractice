---
slug:        fixture-owns-its-state
title:       A fixture owns every piece of state it asserts on
tier:        on-demand
severity:    default
applies_to:  ["**/*.py", "**/*.sh", "**/test_*", "**/tests/**"]
occasion:    "writing a test, fixture or control that reads or edits state it did not create"
gates:       ["review"]
index_clause: "a fixture that inherits real state is testing the environment too"
index_required: false
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

**Owning your scratch directory is not the same as owning what you assert
on.** A fixture can build a perfectly clean room and still reach into a file
whose internals belong to somebody else — a vendored hook, a template, any
copy that arrives from upstream — and anchor on its *shape*: a function name,
a `case`/`esac` branch, "the second line mentioning `HOME`", an exact count of
matching lines. None of that is a contract. Upstream renames the function,
splits the `case` into an `if`/`elif`, grows two substitutions into four, and
the fixture now asserts on a tree where the thing under test and the thing
reached into are both correct. **Anchor on the behaviour the code under test
actually consumes** — the messages a guard prints, the exit codes it returns —
because that is what it was run for, and it is the only part upstream owes
anyone.

**A plant that cannot find its anchor reports SKIPPED with the reason; it
never fails.** That distinction matters more than it sounds. A failure names
the check under test as broken, and that is the wrong culprit: the check was
fine and the plant went stale. A skip naming the anchor it could not find
sends the next reader to the fixture, which is where the work is. A skip is
still not a pass and must never be counted as one — the same discipline the
check runners already print in their own summary lines.

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
**The second way in was found 2026-09-14, in a repository that vendors this
repo's harness.** Its test fixtures planted deliberate breakage into
`freshness-guard.sh` by indexing into the guard's internal shape — find two
`case` lines mentioning a particular shell function; expect exactly two lines
mentioning `HOME` and `path=`. Upstream had since replaced that function and
its `case`/`esac` with an `if`/`elif`, and grown the tilde handling from two
substitutions to four. Three plants asserted and reported the check under test
as broken, on a tree where the check and the guard were both correct; six more
of the same shape were passing only by luck. The fix was to anchor on the
guard's user-facing messages, which is what the check consumes — it *runs* the
guard rather than pattern-matching its source.

**The guard was deliberately not changed to hold its internals still.** A
vendored file's internals are upstream's to move; depending on them is the
fixture's bug, and freezing them to protect one downstream fixture would turn
every future fix into a breaking change.

**Upstream was swept the same day and carries no instance of this shape.**
Three things make it immune rather than lucky, and a future sweep should
re-check all three: this repo has no `tools/checks/` and ships no test
template, so there is no vendored suite here to write such a plant in; the two
harness checks that exercise `freshness-guard.sh` run it as a subprocess and
assert on exit code and stderr; and no fixture anywhere reads a foreign file's
source to locate a shell function, a `case` branch, or a line count.

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

**The two before it are in [AGENTS.md](https://github.com/alex137/BestPractice/blob/staging/AGENTS.md)'s gotchas, and neither
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
