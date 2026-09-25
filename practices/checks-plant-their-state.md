---
slug:        checks-plant-their-state
title:       A check plants every state it asserts about
tier:        on-demand
severity:    default
scope:       any-adopter
applies_to:  ["tools/verify_harness.py", "tools/precedent_check.py", "tools/checks/**", "**/test_*.py", "**/*_test.py", "**/tests/**"]
occasion:    "writing or changing a check, test or gate whose result could depend on the machine it runs on"
gates:       []
index_clause: "plant every state a check asserts -- a verdict that moves on its own is not one"
checked_by:  null
defines:     []
command:     null
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-22"
approved_by: "Morgan, 2026-09-22: \"Your new idea is great. Approved, go update\""
strength:    decided
---

## Rule
**A check builds every state it makes a claim about. If its verdict can
change while the code stays the same, it is measuring the machine rather
than the code — and it is not a check yet.**

Build both worlds and assert each: the one where the behaviour should fire,
and the one where it should stay quiet. **Silence is a behaviour**, so the
quiet case gets its own assertion; a check that only ever asserts the loud
half passes vacuously wherever the loud half happens to be true anyway.

## Detail
**Ambient state is anything the check did not set itself** — the real
filesystem outside its fixture, `$HOME`, the working directory, the clock,
the network, an env var, another process's leftovers, whether some
repository on the disk happens to be dirty today.

**The signature to look for: the check invokes the repository's own live
tool instead of a planted copy of it.** That is the cheap tell, and it is
not by itself the offence — a check whose subject genuinely IS the tree it
is running in reads that tree correctly. The question is narrower: **does
the assertion depend on state the check did not put there?** If yes, plant
it. If the state cannot be planted, the claim cannot honestly be asserted,
and saying so is better than an assertion that will be right by luck.

**"It passed" is not evidence here, and this is the part that gets missed.**
A check like this passes for exactly as long as the ambient state happens
to agree with it, which can be from the day it was written. Green means
nothing until the check has been seen red for the right reason — plant the
failing state on purpose and watch it fail, or the green was never earned.

## Why
**A check that goes red without a code change teaches everyone that red
does not mean anything**, and that is the one thing a gate cannot survive.
Every future failure gets a re-run instead of a look, which is how a real
failure walks through.

**The quieter half is worse.** Before it ever flips, such a check has not
been weakly proving its claim — it has not been proving it at all. It has
been standing in a room where the claim was true for unrelated reasons and
taking the credit.

## Story
**2026-09-22.** `check_archive_line_is_refused_when_the_container_holds_only_copy_work`
ended by running the real reply gate and asserting that it prints the
container-safety requirement. But the gate prints that requirement **only
when the container actually holds unpushed work** — deliberately, with a
comment in
[tools/precedent_gate.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_gate.py)
saying not to nag about a requirement already met.

The suite ran **253 passed, 0 failed. Twice.** Then a session pushed its own
commits, which emptied the container, and the same commit came back **253
passed, 1 failed.** Nothing in the gate had changed. The gate had gone
correctly quiet and the check read the quiet as a failure.

It had also been passing since the day it was written for no better reason
than that whoever wrote it had dirty checkouts at the time — so it had never
once demonstrated the thing it claimed.

The fix used what the check already had: a helper that builds a whole
stubbed engine with a scanner of a chosen answer. It runs the gate against
`engine(1)` for the unsafe container and `engine(0)` for the clean one, and
asserts speech in the first and silence in the second — the negative control
it had never carried. Measured afterwards with the real container in both
states: passing either way.

**A second instance surfaced the same day**, and it makes the point twice
over. `check_endgame_merge_finds_the_silent_drop` was red on
`precedent-beta-v01` in continuous integration and green in every local run
of the same tree. The reading first filed was that the runner's `git`
differed from the container's. **That was wrong, and the correction is the
better lesson**: the failure reproduces on the same `git`, locally, by
removing one thing — the global git identity, which a CI runner does not
have and a session container does. The rehearsal runs
`git merge --no-commit --no-ff`, which refuses without a committer identity,
and its own comment asserted the opposite. Filed and diagnosed at
[todo/todo-2026-09-22-the-endgame-merge-rehearsal-is-red-in-ci-green-locally.md](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-22-the-endgame-merge-rehearsal-is-red-in-ci-green-locally.md).

**Two of these in one day, in one repository, is the argument for a rule
rather than a note on one check.** And the second shows a shape the first
did not. The ambient state need not be anything the check touches — nobody
thought of *whether this machine has a git identity* as an input to a merge
rehearsal, which is exactly why it was never planted. **It also shows how
an unplanted check misleads twice**: first by failing for a reason that is
not its subject, and then by inviting a diagnosis aimed at whatever
environment difference is most visible. A day was pointed at `git`
versions because the check had never said what it actually depended on.

## Install
**`checked_by: null`, and the reason is specific rather than "too hard"**
([checkable-gets-checked](checkable-gets-checked.md)). Two routes were built
far enough to be measured, and both were rejected on what the measurement
said.

**Static detection fires on correct work.** The one concrete signature —
a check invoking this repo's own
[tools/precedent_gate.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_gate.py)
rather than a planted copy — appears in four legitimate check functions in
[tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py)
today: `check_gate_channel`, `check_reply_gate_sees_every_source`,
`check_reply_check_requires_a_destination_for_a_fence_block` and
`check_show_flags_unreachable_materialized_source`. Each reads the live gate
because the live gate is its subject. A check that fires on four correct
things to catch one wrong one is worse than no check.

**Differential detection cannot be made total, and a partial one refutes
this practice.** Running the suspect checks twice under two ambient states
and flagging any verdict that moves is the right shape, and the state is
genuinely perturbable: `checkouts()` in
[tools/precedent_container_safe.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_container_safe.py)
reads `pathlib.Path.home()`, so `$HOME` steers part of it. But that same
function also scans the repo root and the root's siblings unconditionally,
which nothing outside can redirect — so on a machine whose real tree is
dirty, both arms of the differential report unsafe, they agree, and the
guard passes having discriminated nothing. **A guard that silently stops
working depending on the environment is the exact defect named above**, so
building it would be the practice failing itself.

**What holds the line meanwhile** is the fixed check's own negative control:
assert the silence as well as the speech, and an ambient reading that
creeps back in fails one arm or the other. That is a guard on one check
rather than on the rule, which is why this stays `null` rather than
claiming coverage it does not have.
