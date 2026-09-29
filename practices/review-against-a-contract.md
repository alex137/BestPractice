---
slug:        review-against-a-contract
title:       Review code whose failure is silent against a stated contract, and reproduce every finding
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "reviewing code that decides what is skipped, cached, held or refused"
gates:       []
index_clause: "give each reviewer a one-line contract; a finding counts once reproduced"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-29"
approved_by: "Alex, 2026-09-29 -- \"Yes on all your recommendations.  Let's do all 7 practices\""
strength:    decided
---
## Rule
Code that decides **what not to do** — a cache key, a skip ledger, a
gate that holds a result, a filter that refuses — fails silently: a
wrong answer looks exactly like a right one. Review it against a
**contract stated in one line**, such as *"a skip must never hold when
the output could differ"* or *"a key must move whenever the result
can"*. Give each reviewer that line, a sandbox, and one instruction:
**a finding counts only once it is reproduced** by an experiment that
shows the contract broken.

## Detail
**Split the review by what can break, not by file.** One reviewer per
mechanism (how the key is computed, what the hook records, how facts are
matched, how the runner orders and stops), each holding the same
contract. A reviewer who owns a mechanism reads it all the way down;
one who owns a file stops at its edge.

**A reproduced finding is a test.** The experiment that confirmed it —
a toy repository, a planted edit, a run beside a full run — becomes the
regression case once the fix lands, and it must fail on the code before
the fix ([control-asserts-which-failure](control-asserts-which-failure.md)).

**Unreproduced suspicions are reported separately**, as leads, never
mixed into the findings. A list of plausible concerns is easy to write
and costs the reader the work of telling which are real.

This practice has no repository-level check (`checked_by: null`):
whether a review was run against a contract is a fact about how the
review was done, which the files do not record.

## Why
Ordinary review asks "does this look right", and silent-failure code
always looks right: the tests its author wrote pass, and every output
is plausible. A contract turns the question into something a reviewer
can try to break, and reproduction keeps the findings to the ones that
are true.

## Story
In the originating repository, a session built a cache key that follows
the code a computation reaches, and two ledgers that skip work whose
inputs have not changed. Every test written alongside them passed. Four
reviewers were then each given one mechanism, a one-line contract and a
sandbox, and told to confirm every finding by experiment. All four found
real bugs, and almost every finding came back reproduced: a default
argument the key did not follow, file hashes taken at the wrong moment, a
ledger that replayed eight of nine real failures as passes. The one
ledger that could not be made sound was removed.

## Install
Nothing to install. When the code under review decides what is skipped,
cached, held or refused, write its contract as one line before the
review starts, give every reviewer that line and a place to run
experiments, and accept only reproduced findings.
