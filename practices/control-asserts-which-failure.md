---
slug:        control-asserts-which-failure
title:       A test that expects a failure must assert which failure, not merely that one happened
tier:        on-demand
severity:    default
applies_to:  ["tools/**/*.py", "**/tests/**", "**/*_test.py", "**/test_*.py"]
occasion:    "writing a test, fixture or control that proves a guard fires"
gates:       ["review"]
index_clause: "a non-zero exit is not evidence; assert the message that guard prints"
checked_by:  null
defines:     ["positive control", "negative control"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-07"
approved_by: "Morgan (2026-09-07)"
---
## Rule
When a test exists to prove that a guard **refuses**, asserting that
something failed is not enough. Assert **which** failure: the message that
guard prints, the specific exit path, the named condition. A non-zero exit
says only that the run did not reach the end, and a fixture elaborate enough
to exercise a guard is elaborate enough to break for three other reasons
first.

Two halves, and skipping either one leaves the test hollow:

1. **The positive control asserts the guard's own words.** Not
   `returncode != 0`, not "an exception was raised" — a string only the
   guard under test emits. If two guards could both produce the observed
   failure, the test does not distinguish them and must be made to.
2. **The negative control proves the assertion can fail.** Remove or neuter
   the guard, re-run, and watch the case go red. A control that passes with
   the guard deleted is measuring something else.

**A guard that cannot establish its own inputs must say so, never return a
clean result.** This is where a hollow control does its real damage: a guard
whose input read silently produced nothing will pass every test that only
checks "did it complain when it should" — because it complains for the
planted case by accident, or does not run at all and the fixture fails
elsewhere. Make "I could not evaluate this" a distinct, loud outcome
([fail-gracefully](fail-gracefully.md)), and assert *that* string too.

## Why
A test's whole value is the set of futures it rules out. "Something went
wrong" rules out almost nothing, because in a fixture that builds
repositories, writes config and shells out to a tool, nearly every mistake
also produces a non-zero exit. The test then passes for the wrong reason,
and — this is the part that costs — it passes *consistently*, so nobody ever
looks at it again. A flaky hollow test gets investigated; a stable hollow
test is trusted forever.

The failure is invisible in exactly the situation the test was written for.
Nobody writes a control for a guard they doubt; they write it for a guard
they have just built and believe in. So the run is expected to be green, a
green result confirms the belief, and the one question that would expose the
hollowness — *did it fail for the reason I think?* — is the question
confidence stops you asking.

This is why the discipline is cheap and the alternative is not. Reading the
message costs one line in the assertion. Not reading it costs a guard that
looks tested, ships, and is discovered inert only when the thing it was
supposed to prevent actually happens.

## Story
Three incidents in two days, in one repository, all with the same shape.

**A guard that passed its own control while doing nothing.** A sync tool was
given a guard refusing to delete a rule the repository had already
published. The code read its input as a list; the input was a dictionary
keyed by slug. The misread produced an empty set, and a fallback — *"if I
cannot work out the rule set, return nothing"* — swallowed it. The guard was
inert. Its positive control still passed, because the fixture had deleted a
source's only practice and tripped a **different, pre-existing** guard. The
test proved a refusal happened. It did not prove which one, and the two were
not the same. Worth noting what would *not* have helped: the value's shape
was already documented at its producer, on the first line of that function's
docstring. The information was there and was misread; a second copy of it at
the call site would have been a third place to drift.

**A refusal read as a pass, on a completely unrelated error.** A fixture
built to prove `checkin.py update` refuses while a branch is pinned ran the
*upstream* script from a consumer directory. That script resolves its root
from its own file location, so the consumer's install was never exercised.
The fixture saw a non-zero exit and scored a pass; the actual message was
`no upstream.commit recorded in the manifest` — an unrelated missing-fixture
error. Rewriting every case to read the message turned 4 of 8 red
immediately.

**A negative control that could not go red.** In the same week, a swallowed
exit code from a git helper made a failing `git checkout` in a dirty tree
look like a passing test, so a broken control was indistinguishable from a
working one. "The command reported nothing" is no evidence at all.

## Install
Write every failure assertion against a string the guard itself prints, and
put that string somewhere both the guard and the test read from if it is
long. Then delete the guard and run the test: if it stays green, the test is
not testing it. Where a fixture shells out to a tool, confirm the tool is
resolving the paths you think it is — print them once while writing the
test — because a fixture that never reaches the code under test still exits
non-zero for its own reasons.

A reviewer's version of the same question, cheap to ask on any diff that
adds a control: *what else could produce this failure?* If the answer is
"several things", the assertion is not finished.
