---
slug:            gotcha-2026-09-21-a-green-local-verify-harness-run-does-not-mean-green-ci
status:          live
noted:           2026-09-21
severity:        null
retired:         null
retires_when:    null
---
## Symptom

[tools/verify_harness.py](../tools/verify_harness.py) passes locally with
`0 failed`, and the deep-check CI job fails anyway — with a traceback
instead of a verdict, before a single `PASS:` line is printed.

## Story

CI does not run [tools/verify_harness.py](../tools/verify_harness.py) the way a
session runs it. The
deep-check workflow splits it into two jobs using
`PRECEDENT_CHECK_ONLY` / `PRECEDENT_CHECK_SKIP`, because one check
(`check_precedent_check_fires`) was about half the total runtime
([spec/VERIFY_HARNESS_PERFORMANCE.md](../spec/VERIFY_HARNESS_PERFORMANCE.md)).
Those variables are set **only** in CI. A plain local run sets neither, so
the entire filter path — including every behaviour that depends on a check
being replaced by a stand-in — is code no local run ever executes.

On 2026-09-21 that gap hid a crash in the filter itself. A filtered-out
check was replaced by a stand-in returning `None`, and ten call sites are
written as `check('<name>', *check_foo())`, so `*None` raised
`TypeError: Value after * must be an iterable, not NoneType` at the first
of them. The full local suite reported `244 passed, 0 failed`; both sharded
CI jobs died before their first verdict. The session that hit it had run
the complete deep check, seen it green, and opened a pull request to `main`
on that basis.

Worth noting what the immediately preceding commit was:
*"Make the source clone current first, and stop a skip reporting success"*.
An earlier version of the stand-in returned something truthy, so a skipped
check reported **PASS** — a real bug, correctly fixed. The fix replaced it
with `None`, trading a silent false pass for a loud crash, and nothing
tested either behaviour because nothing local runs that path at all.

**Update, 2026-09-22 — and do NOT try to emulate CI's environment.** The
sensible-looking next step is to run the suite with the machine's git config
nulled, on the theory that CI is "a machine with no git identity". Measured:
it is not. Pointing `GIT_CONFIG_GLOBAL` at an empty file with an empty `HOME`
makes two checks fail — the two about the commit-identity backstop — that pass
in real CI on the same commit. `GIT_CONFIG_GLOBAL=/dev/null` does not even
work: this git version rejects it outright with
`fatal: bad config line 1 in file /dev/null`, several minutes into the run.

So a "hermetic environment" job would manufacture failures CI does not have,
which is worse than not having one. **The shard SHAPE is reproducible locally
and worth reproducing; the ENVIRONMENT is not.** What actually catches the
class of bug this entry describes is making fixture setup commands fail
loudly, which is now what they do.

## Fix

**Before trusting a green deep check ahead of a push, run the harness the
way CI runs it** — both shards, not just the default invocation:

    PRECEDENT_CHECK_ONLY=check_precedent_check_fires python3 tools/verify_harness.py
    PRECEDENT_CHECK_SKIP=check_precedent_check_fires python3 tools/verify_harness.py

Each takes well under the full suite's runtime, and between them they cover
the filter path the default run skips entirely.

The specific crash above is fixed and now has its own control
(`check_filtered_check_does_not_break_the_unpack_family`): a filtered check
returns a sentinel that `check()` records as N/A, so it can neither crash
the unpack nor report success. **The general trap is still live** — any
other behaviour that only differs under the filter remains invisible to a
default local run.
