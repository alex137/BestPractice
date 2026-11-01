---
slug:        quick-tier-is-closed
title:       "Nothing new runs before a push without the person's own words, and its time"
tier:        on-demand
severity:    default
applies_to:  ["tools/precedent_push_check.py", "tools/verify_harness.py", "tools/harness/**", "tools/checks/**", "local/tools/checks/**", "templates/hooks/**", ".claude/hooks/**"]
applies_to_why: "Fires where a check or a test could be wired to run before a push: the push check itself, the harness (verify_harness.py and, since its split into area files, tools/harness/**), check scripts and their tests, and the hooks that start a check. Decided: 2026-10-16, when the practice landed."
occasion:    "adding a test or a check, or wiring one to run before a push"
gates:       ["review"]
gates_why:   "Where a new test runs is chosen while the change is being designed; `review` is that moment, before it is wired into the quick check."
index_clause: "new tests go in the full check; before a push only on their words and time"
index_required: false
checked_by:  null
defines:     ["quick tier", "quick checks"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-16"
approved_by: "Morgan, 2026-10-16: \"LET'S BAN ALL NEW TESTS BEFOREHAND EXCEPT WHEN EXPLICITLY DIRECTLY VERBALLY AUTHORIZED\", and \"note any new test beforehand needs to be explicitly approved and also have a time estimate and you need to strongly encourage the person to put it after and in debut etc\"."
strength:    decided
---
## Rule
**A new test or check runs in the full check, never before a push**: the
full run on the landing branch when it is asked for, and around the move
into `main`. **The quick tier**, whose checks are **the quick checks**, is
what runs before a push: only the bare essentials, the leak gate, the commit
checks and the per-file checks.

**Putting one before a push takes the person's own words asking for that
check, and its time.** Before asking, measure what it takes, tell them in
seconds, and **urge them to leave it to the full check instead**: a landing that
waits on it waits every time, and the full tier runs it anyway. A session's
own judgment that a check is cheap never counts, and neither does a general
go-ahead on the work around it.

**Then record it in the same commit:** the check's name, the person's
quoted words with their date, and its seconds, in `BASIC_CHECKS_APPROVED` in
[tools/precedent_push_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_push_check.py), and its name in
`check_quick_tier_is_closed`'s list.

## Detail
**What enforces it.** `check_quick_tier_is_closed` in
[tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py) fails when the quick tier's
checks differ from its list, when an entry has no quoted words and date,
when an entry added after 2026-10-16 has no time, or when the per-file step
starts a test, the harness or the practice checks. A new harness test also
lands with its recorded time: the per-file step refuses one without it and
names `python3 tools/verify_harness.py --record-new-times`.

**Where a new test goes instead.** Into the harness or a check's own test,
which the full tier runs: the full run on the landing branch
(`precedent_branches.py --run-tests`), then GitHub's test after the move
into `main`, or the full local suite on `main` where
that test is not due.

## Why
Every check before a push is paid on every landing, by everyone, forever,
and it catches nothing the full tier would not catch a little later. A
landing that takes minutes is a landing people put off.

## Story
On 2026-10-11 the quick check began running the harness tests a change
reaches, inside a one-minute budget. Five days later a landing took 218
seconds of quick checks: the practice checks on the changed files took 42,
and the harness tests 92, because the timing list the budget read was a
hundred tests out of date and counted each missing one as 0.42 seconds.
Morgan moved every test to the Debut and around Produce, closed the quick
tier, and asked that any new entry come with his words, its time, and a
case for the Debut first. The record is
[spec/TESTS_RUN_AT_THE_DEBUT_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/TESTS_RUN_AT_THE_DEBUT_PLAN.md).


**2026-10-17: the Rule names its terms.** "Quick tier" and "quick checks"
were used across the engine with no glossary entry; the Rule's sentence on
what runs before a push now names them, and `defines:` lists them. The
wording was chosen by the session under Morgan's delegation of 2026-10-17: "Fix the other issues you found including the checks that never run. Tell me what you decide. I will be offline so don't wait for me. Approved, act, and Booked."

## Install
Nothing to install: it ships with the engine. A repository whose own push
check runs extra steps before a push applies the same rule to them.
