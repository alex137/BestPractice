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
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-17"
approved_by: "S. Alexander Jacobson, 2026-09-17 -- his own direction in dependent repo #1, adopted verbatim as the rule: \"As a general practice, we should not start long tasks without checking with the user about doing so and without answering easy questions first.\" Checked in from that repo the same day."
strength:    decided
---
## Rule
Three parts. **(1) Answer the easy questions in a message before starting
anything long.** A conceptual question is answered from what is already
known, in the same turn, before any long run is launched; the run never
gates the answer. **(2) A task that will run longer than a few minutes —
a cold solve, a search family, a re-solve cascade, a whole-tree gate —
is proposed, not started:** say what it is, how long it will take (from
the tool's own cost line), what it blocks and what it does not, and get
the go-ahead. The exceptions are the checks a commit needs on the files
the turn touched, and a run the person has already asked for by name.
**(3) When idle on a wait, say what the wait is for, what it will change,
and how to stop it** — never a bare "still running". A background task
nobody asked for is stopped, not waited on.

## Detail
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

## Install
Adopt the rule in the working-conventions file and name the cost-line
convention it depends on (every heavy tool prints its estimated duration
before it runs; see
[slow-steps-report-and-cache](slow-steps-report-and-cache.md) for the
progress line and the memo, and
[scripts-assert-properties](scripts-assert-properties.md) for the
model-side discipline). A wait longer than a minute reports elapsed and
remaining time on its own.
