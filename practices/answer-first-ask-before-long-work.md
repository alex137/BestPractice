---
slug:        answer-first-ask-before-long-work
title:       Answer the easy questions first; propose a long task before starting it; an open question never pauses the work
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "a turn that could start a computation, search or build lasting longer than a few minutes"
gates:       []
index_clause: "easy answers first; a long run is proposed with its cost -- never just started"
checked_by:  null
defines:     ["long task"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan F, drafted 2026-10-05, moved from the shared set precedent-shared-working-style; merged in PR #879 on 2026-10-05; part 2's exception narrowed to the quick checks by Morgan F, 2026-10-07"
strength:    decided
---
## Rule
Four parts. **(1) Answer the easy questions in a message before starting
anything long** — in the same turn; the long run never gates the answer.
**(2) A task that will run longer than a few minutes is proposed, not
started:** what it is, how long from the tool's own cost line, what it
blocks and what it does not, then the go-ahead. The exceptions are the
quick checks a commit needs on the files the turn touched, never a
whole suite, and a run already asked for by name. **(3) When idle on a wait, say what the wait is for,
what it will change, and how to stop it** — never a bare "still running".
A background task nobody asked for is stopped, not waited on.
**(4) An open question is not a stopping point:** ask it early and keep
working on everything its answer does not touch.

## Detail
**What part 1 means by an easy question:** one answered from what is already
known, without waiting on a run. **What part 2 means by a long task:** a
cold solve, a search family, a re-solve cascade, a whole-tree gate. Both
were in the Rule until 2026-09-21 (see `## Story`).

"A few minutes" is the boundary at which a person would rather have been
asked: below it the run is cheaper than the exchange; above it the run
is a decision about their time and their machine. The proposal is one
message: the task, its estimated duration from a measured cost line
(never a guess), what the person can and cannot do meanwhile, and the
question. A run that was authorized once is not authorized again after
its inputs change — a merge that re-keys a cache is a new proposal.

**What part 4 means by a question that may stop the work:** sort pending
questions into blockers and everything else. A blocker is one where
proceeding under any assumption would be unsafe, spend real money or touch
production the wrong way, or make the delivered work useless if the guess is
wrong -- only those justify stopping with nothing delivered. Everything else
is non-blocking: do the work that doesn't depend on the answer and the work
that comes out the same either way, then ask, then carry on with whatever's
still independent. Ask as soon as the question is formed rather than saving
it for a summary, since the person is often away when the answer would be
most useful; where the answer would change work already done, say so when
asking, so the cost of each option is visible.

## Why
A long run started unasked costs twice: the person waits for something
they did not choose, and the easy answers they did ask for wait behind
it. And a wait nobody explained is indistinguishable from a hang, so the
person either interrupts healthy work or sits through dead work.
Part 4 is the same cost from the other side: the answer to an open question
should arrive while work is still in flight, and a question asked only at the
end of a session has nowhere useful to land.

## Story
A session launched an hours-long re-solve while four conceptual
questions sat unanswered, then sat on a ninety-minute cold solve after a
merge invalidated a cache, before answering a one-line question about
the merge itself. The person's direction, adopted as the rule: do not
start long tasks without checking first, and answer the easy questions
before anything else.


**Rule compressed 2026-09-21**, in the reduction pass recorded in
[todo-2026-09-21-resident-cap-was-measured-on-the-wrong-shape.md](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-21-resident-cap-was-measured-on-the-wrong-shape.md).
208 tokens -> 124. All three parts stayed; what moved into `## Detail` is
the pair of definitions the Rule was carrying inline -- what counts as an
easy question, and the four examples of a long task. The exceptions stayed
in the Rule, because a session reads them at the moment it is deciding
whether to ask.

**Moved to `precedent-shared-working-style` and back, same day, 2026-09-23.**
A cross-repo practice-placement review moved this out of universal, on the
reasoning that it is squarely that set's own subject. The disclosed cost at
the time -- reaching only a repo that declares `precedent-shared-working-style`,
rather than every Precedent consumer including the downstream repo that
contributed it -- turned out to be worse than a smaller audience:
`verify_harness.py --as-ci`'s consumer-fixture check found the deduplication
record itself was false for a plain consumer resolving only universal, which
is most of them -- `in_force_at:` pointed at a slug that does not resolve IN
FORCE anywhere that consumer can see. The tool that runs every other kind of
move refuses exactly this direction (`--from universal`) for exactly this
reason, which this incident confirms rather than merely asserts. Reverted
the same day, Morgan F: stays universal, `tier: resident`, as before.

Later on 2026-09-23 (commit `73ad9f14`) this universal copy was withdrawn
after all and pointed at the working-style set's copy, which was the one in
force from then. **2026-10-05: this file is the live copy again**, moved
back as the working-style set folded away (Morgan F, strength: decided).

**2026-10-01, part (4) absorbed from `nonblocking-questions`**, in the
reduction pass recorded in BestPractice's
[todo-2026-09-30-session-file-cut-to-4000.md](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-30-session-file-cut-to-4000.md)
("Reduction pass review, 2026-10-01"). The two resident rules were one
subject -- what a session does with its time while a person has not yet
answered -- and loading both on every turn paid for two headers and two
framings of it. Its Rule became part (4) and its blocker test moved into
`## Detail` whole; its file is `status: deduplicated` and points here.
Approved by Morgan F, 2026-10-01: *"Question 3 - all are great, approved"*
(strength: decided).

**2026-10-07, part (2)'s exception narrowed to the quick checks.** A
session started BestPractice's whole test suite by hand to double-check
work bound only for pre-staging, whose own push check takes seconds. It
quoted fifteen to twenty-five minutes from memory; a third of the way in,
twenty-five minutes had gone, and the one-process run takes about forty.
It had read "the checks a commit needs" as covering the whole suite. Morgan
asked how to stop it happening again, and approved all three answers
(*"Yes, make those changes"*, strength: decided): the suite now prints what
it costs before it starts, a full run started by hand refuses without
`--because` quoting the person's go-ahead, and this exception names the
quick checks.

## Install
Adopt the rule in the working-conventions file and name the cost-line
convention it depends on (every heavy tool prints its estimated duration
before it runs; see
[slow-steps-report-and-cache](https://github.com/alex137/BestPractice/blob/staging/practices/slow-steps-report-and-cache.md) for the
progress line and the memo, and
[scripts-assert-properties](https://github.com/alex137/BestPractice/blob/staging/practices/scripts-assert-properties.md) for the
model-side discipline). A wait longer than a minute reports elapsed and
remaining time on its own.
