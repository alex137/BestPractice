---
slug:        verify-postcondition
title:       Verify the postcondition, not the command
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "after any state-changing operation"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 32
---
## Rule
After any state-changing operation, check **the state you wanted**,
not that the command reported success. Name the postcondition before you run
the command — *"no unpushed commits on any branch"*, *"the gate passed"*,
*"the file contains X"* — and then test that, independently of whatever the
command printed.

## Detail
Two traps deserve naming because they produce confident, wrong success
messages:

- **A pipeline's exit status is its last command's.** `check | tail && publish`
  does not gate on `check`. The gate can print FAIL in plain sight and the
  publish still proceeds. Run gates bare and test `$?`; if you pipe for
  readability, capture the status first or use the shell's pipe-status
  facility.
- **A command with an explicit target acts on the target you named, not the
  context you are in.** Publishing by naming a branch publishes *that* branch,
  whether or not it is the one you have been working on. If it has not moved,
  the operation succeeds as a no-op and says so.

## Why
Neither command malfunctioned. Both did exactly what they were literally asked
to do. The defect was reading *"the command ran"* as *"my intent was
achieved"* — and the more precisely a command is targeted, the more completely
it ignores your context, which is a virtue right up until your context is
wrong.

Note what actually caught it: an **independent check** — a hook comparing local
branches against the remote — not the session's own review. Self-reported
completion cannot catch a wrong premise about what "complete" meant. That is
the argument for having such a check at all, and for treating its output as
information rather than noise.

## Story
Two incidents in one session, one root cause. A gate chained through a
pipe let a failing check reach the shared trunk. Then work was committed on the
wrong branch and "published" by naming the intended branch explicitly — which
had not moved, so the push succeeded, reported success, and left the commit
sitting unpublished somewhere else. The session reported the work delivered.

The second incident is the sharper one, because the misleading part was the
*success*. A failure would have been investigated. A green line about an
operation you did not intend gets skimmed, and the more automated the reporting,
the more likely it is skimmed. An agent narrating its own work is especially
exposed here: it produces the summary from the same premises that produced the
mistake, so the summary inherits the error and reads as confirmation.

## Install
For each operation that matters, write the check next to the
action:

- **Gates:** run bare, test the exit status. Never gate on a pipeline.
- **Before committing:** confirm which branch you are on.
- **Before declaring anything delivered:** enumerate every local branch against
  its remote and require the difference to be empty — the postcondition is
  "nothing unpublished anywhere", not "the publish command printed something".
- **In general:** if you cannot state the postcondition, you do not yet know
  what the command was for.

Cheap and worth it: end a work session by re-deriving the finished state from
the repository rather than from your own transcript.

**Related.** Practice 6 (conventions become audits) — this is the audit for
"did the thing actually land". Practice 20 (mistakes become rules) produced it,
from two failures with one root cause folded into one widened rule rather than
two narrow ones, per that practice's proportionality guard.
