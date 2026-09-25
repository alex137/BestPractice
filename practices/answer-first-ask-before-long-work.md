---
slug:        answer-first-ask-before-long-work
title:       Answer the easy questions first; propose a long task before starting it
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "a turn that could start a computation, search or build lasting longer than a few minutes"
gates:       []
index_clause: "easy answers first; a long run is proposed with its cost -- never just started"
checked_by:  null
defines:     ["long task"]
status:      deduplicated
in_force_at: answer-first-ask-before-long-work
supersedes:  []
overrides:   null
added:       "2026-09-17"
approved_by: "S. Alexander Jacobson, 2026-09-17 -- his own direction in dependent repo #1, adopted verbatim as the rule: \"As a general practice, we should not start long tasks without checking with the user about doing so and without answering easy questions first.\" Checked in from that repo the same day."
strength:    decided
---
## Rule
Three parts. **(1) Answer the easy questions in a message before starting
anything long** — in the same turn; the long run never gates the answer.
**(2) A task that will run longer than a few minutes is proposed, not
started:** what it is, how long from the tool's own cost line, what it
blocks and what it does not, then the go-ahead. The exceptions are the
checks a commit needs on the files the turn touched, and a run already
asked for by name. **(3) When idle on a wait, say what the wait is for,
what it will change, and how to stop it** — never a bare "still running".
A background task nobody asked for is stopped, not waited on.

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

## Why
A long run started unasked costs twice: the person waits for something
they did not choose, and the easy answers they did ask for wait behind
it. And a wait nobody explained is indistinguishable from a hang, so the
person either interrupts healthy work or sits through dead work.

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

## Install
Adopt the rule in the working-conventions file and name the cost-line
convention it depends on (every heavy tool prints its estimated duration
before it runs; see
[slow-steps-report-and-cache](slow-steps-report-and-cache.md) for the
progress line and the memo, and
[scripts-assert-properties](scripts-assert-properties.md) for the
model-side discipline). A wait longer than a minute reports elapsed and
remaining time on its own.

Also landed in the shared set `precedent-shared-working-style` on 2026-09-23, approved there by Morgan F. Kept ACTIVE here, not deduplicated: universal is the one level every Precedent consumer resolves, and a plain universal-only consumer never resolves a pointer into `precedent-shared-working-style` -- deduplicating this copy would leave the rule in force nowhere for them (the failure `verify_harness.py --as-ci`'s consumer-fixture check exists to catch, and did, 2026-09-23). Both copies are genuinely in force; review both when editing either. Withdraw this copy later, deliberately, with `--dedupe-only --accept-reach-loss` once the audience that matters has taken `precedent-shared-working-style`.

Withdrawn from universal on 2026-09-23, deliberately, with --accept-reach-loss: deduplicated here; the rule is in force only from the shared set `precedent-shared-working-style` now. A consumer resolving only universal no longer gets it.
